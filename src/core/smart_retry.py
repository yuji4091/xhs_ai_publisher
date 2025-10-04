"""
自动重试和错误恢复系统 - 减少人工干预
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import logging

from src.core.logger import logger


class RetryStrategy(Enum):
    """重试策略"""
    IMMEDIATE = "immediate"      # 立即重试
    LINEAR = "linear"           # 线性退避
    EXPONENTIAL = "exponential" # 指数退避
    RANDOM = "random"          # 随机退避


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    jitter: bool = True       # 是否添加随机抖动


@dataclass
class RetryResult:
    """重试结果"""
    success: bool
    attempts: int
    total_time: float
    last_error: Optional[Exception] = None
    result: Any = None


class SmartRetry:
    """智能重试管理器"""

    def __init__(self):
        self.retry_stats: Dict[str, Dict[str, Any]] = {}

    async def execute_with_retry(self, func: Callable, *args,
                                config: RetryConfig = None,
                                operation_name: str = "operation",
                                **kwargs) -> RetryResult:
        """执行带重试的函数"""
        if config is None:
            config = RetryConfig()

        start_time = time.time()
        last_error = None

        for attempt in range(1, config.max_attempts + 1):
            try:
                logger.info(f"执行 {operation_name} (尝试 {attempt}/{config.max_attempts})")

                result = await func(*args, **kwargs)

                total_time = time.time() - start_time
                self._record_success(operation_name, attempt, total_time)

                return RetryResult(
                    success=True,
                    attempts=attempt,
                    total_time=total_time,
                    result=result
                )

            except Exception as e:
                last_error = e
                total_time = time.time() - start_time

                logger.warning(f"{operation_name} 第{attempt}次尝试失败: {e}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < config.max_attempts:
                    delay = self._calculate_delay(config, attempt)
                    logger.info(f"{operation_name} 将在 {delay:.1f} 秒后重试")
                    await asyncio.sleep(delay)
                else:
                    self._record_failure(operation_name, attempt, total_time, str(e))

        # 所有重试都失败了
        return RetryResult(
            success=False,
            attempts=config.max_attempts,
            total_time=time.time() - start_time,
            last_error=last_error
        )

    def _calculate_delay(self, config: RetryConfig, attempt: int) -> float:
        """计算重试延迟"""
        if config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0.0
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * attempt
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (2 ** (attempt - 1))
        elif config.strategy == RetryStrategy.RANDOM:
            delay = config.base_delay + random.uniform(0, config.base_delay * 2)
        else:
            delay = config.base_delay

        # 限制最大延迟
        delay = min(delay, config.max_delay)

        # 添加随机抖动
        if config.jitter:
            delay *= (0.5 + random.random() * 0.5)  # 0.5-1.0倍

        return delay

    def _record_success(self, operation: str, attempts: int, total_time: float):
        """记录成功统计"""
        if operation not in self.retry_stats:
            self.retry_stats[operation] = {
                'total_attempts': 0,
                'success_count': 0,
                'failure_count': 0,
                'avg_attempts': 0,
                'avg_time': 0
            }

        stats = self.retry_stats[operation]
        stats['total_attempts'] += attempts
        stats['success_count'] += 1

        # 更新平均值
        total_success = stats['success_count']
        stats['avg_attempts'] = (stats['avg_attempts'] * (total_success - 1) + attempts) / total_success
        stats['avg_time'] = (stats['avg_time'] * (total_success - 1) + total_time) / total_success

    def _record_failure(self, operation: str, attempts: int, total_time: float, error: str):
        """记录失败统计"""
        if operation not in self.retry_stats:
            self.retry_stats[operation] = {
                'total_attempts': 0,
                'success_count': 0,
                'failure_count': 0,
                'avg_attempts': 0,
                'avg_time': 0,
                'last_errors': []
            }

        stats = self.retry_stats[operation]
        stats['total_attempts'] += attempts
        stats['failure_count'] += 1

        # 记录最近的错误
        stats['last_errors'] = (stats.get('last_errors', []) + [error])[-5:]  # 只保留最近5个错误

    def get_stats(self, operation: str = None) -> Dict[str, Any]:
        """获取统计信息"""
        if operation:
            return self.retry_stats.get(operation, {})
        else:
            return dict(self.retry_stats)

    def reset_stats(self, operation: str = None):
        """重置统计信息"""
        if operation:
            self.retry_stats.pop(operation, None)
        else:
            self.retry_stats.clear()


class ErrorRecoveryManager:
    """错误恢复管理器"""

    def __init__(self):
        self.recovery_strategies: Dict[str, Callable] = {}
        self.error_patterns: Dict[str, Dict[str, Any]] = {}

    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """注册错误恢复策略"""
        self.recovery_strategies[error_type] = strategy

    def register_error_pattern(self, error_pattern: str, recovery_action: str,
                             max_occurrences: int = 5, time_window: int = 300):
        """注册错误模式"""
        self.error_patterns[error_pattern] = {
            'recovery_action': recovery_action,
            'max_occurrences': max_occurrences,
            'time_window': time_window,
            'occurrences': []
        }

    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """处理错误并尝试恢复"""
        error_type = type(error).__name__
        error_msg = str(error)

        logger.error(f"发生错误: {error_type} - {error_msg}")

        # 检查是否匹配已知错误模式
        for pattern, config in self.error_patterns.items():
            if pattern.lower() in error_msg.lower():
                if await self._handle_pattern_error(pattern, config, error, context):
                    return True

        # 尝试通用错误恢复策略
        if error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_type]
                result = await strategy(error, context)
                if result:
                    logger.info(f"错误恢复成功: {error_type}")
                    return True
            except Exception as recovery_error:
                logger.error(f"错误恢复失败: {recovery_error}")

        return False

    async def _handle_pattern_error(self, pattern: str, config: Dict[str, Any],
                                  error: Exception, context: Dict[str, Any]) -> bool:
        """处理模式匹配的错误"""
        now = datetime.now()

        # 清理过期记录
        config['occurrences'] = [
            occ for occ in config['occurrences']
            if (now - occ).seconds < config['time_window']
        ]

        # 记录当前错误
        config['occurrences'].append(now)

        # 检查是否超过阈值
        if len(config['occurrences']) >= config['max_occurrences']:
            logger.warning(f"错误模式 '{pattern}' 在 {config['time_window']} 秒内发生 {len(config['occurrences'])} 次")

            # 执行恢复动作
            recovery_action = config['recovery_action']
            if recovery_action == 'restart_browser':
                return await self._restart_browser(context)
            elif recovery_action == 'switch_proxy':
                return await self._switch_proxy(context)
            elif recovery_action == 'wait_and_retry':
                await asyncio.sleep(60)  # 等待1分钟
                return True

        return False

    async def _restart_browser(self, context: Dict[str, Any]) -> bool:
        """重启浏览器"""
        try:
            if 'browser_manager' in context:
                browser_mgr = context['browser_manager']
                await browser_mgr.close()
                await browser_mgr.initialize()
                logger.info("浏览器重启成功")
                return True
        except Exception as e:
            logger.error(f"浏览器重启失败: {e}")

        return False

    async def _switch_proxy(self, context: Dict[str, Any]) -> bool:
        """切换代理"""
        try:
            if 'proxy_service' in context and 'user_id' in context:
                proxy_service = context['proxy_service']
                user_id = context['user_id']

                # 获取新代理
                new_proxy = await proxy_service.get_next_available_proxy(user_id)
                if new_proxy:
                    logger.info(f"切换到新代理: {new_proxy.host}:{new_proxy.port}")
                    return True
        except Exception as e:
            logger.error(f"代理切换失败: {e}")

        return False


# 全局实例
smart_retry = SmartRetry()
error_recovery = ErrorRecoveryManager()


# 预注册常见错误恢复策略
def setup_default_error_recovery():
    """设置默认错误恢复策略"""

    # 网络错误恢复
    async def network_error_recovery(error, context):
        await asyncio.sleep(5)  # 等待网络恢复
        return True

    error_recovery.register_recovery_strategy('ConnectionError', network_error_recovery)
    error_recovery.register_recovery_strategy('TimeoutError', network_error_recovery)

    # 浏览器错误恢复
    async def browser_error_recovery(error, context):
        if 'browser_manager' in context:
            browser_mgr = context['browser_manager']
            await browser_mgr.close()
            await asyncio.sleep(2)
            await browser_mgr.initialize()
            return True
        return False

    error_recovery.register_recovery_strategy('BrowserError', browser_error_recovery)

    # 注册常见错误模式
    error_recovery.register_error_pattern(
        '验证码错误', 'wait_and_retry', max_occurrences=3, time_window=600
    )
    error_recovery.register_error_pattern(
        '网络超时', 'wait_and_retry', max_occurrences=5, time_window=300
    )
    error_recovery.register_error_pattern(
        '浏览器崩溃', 'restart_browser', max_occurrences=2, time_window=600
    )


# 使用示例
async def demo():
    """演示函数"""
    print("开始智能重试演示...")

    # 示例函数 - 模拟有时会失败的操作
    async def unreliable_operation(attempt_num):
        if attempt_num < 3:  # 前两次失败
            raise ConnectionError("网络连接失败")
        return f"操作成功！(第{attempt_num}次尝试)"

    # 使用智能重试
    result = await smart_retry.execute_with_retry(
        unreliable_operation,
        0,  # 参数
        config=RetryConfig(max_attempts=5, strategy=RetryStrategy.EXPONENTIAL),
        operation_name="网络请求"
    )

    print(f"重试结果: 成功={result.success}, 尝试次数={result.attempts}, 总时间={result.total_time:.2f}s")
    if result.success:
        print(f"结果: {result.result}")
    else:
        print(f"最终错误: {result.last_error}")

    # 查看统计
    stats = smart_retry.get_stats('网络请求')
    print(f"统计信息: {stats}")


if __name__ == "__main__":
    # 设置默认错误恢复
    setup_default_error_recovery()

    # 运行演示
    asyncio.run(demo())