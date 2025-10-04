# 小红书AI发布助手 - Copilot Instructions

## Architecture Overview

This is a **dual-interface automation tool** for Xiaohongshu (小红书) content publishing with both PyQt5 desktop and FastAPI web interfaces. The core automation is built on Playwright browser automation with anti-detection features.

### Key Components

- **Dual Entry Points**: `main.py` (PyQt5 desktop) and `src/web/app.py` (FastAPI web)
- **Core Automation**: `src/core/write_xiaohongshu.py` handles Playwright-based publishing
- **Browser Management**: `src/core/browser_manager.py` with anti-detection stealth scripts
- **Data Layer**: SQLAlchemy models in `src/core/models/` with SQLite backend
- **Configuration**: Dual config system - `src/config/config.py` (simple) and `src/core/config.py` (dataclass-based)

## Critical Development Patterns

### 1. Anti-Detection Browser Setup
All browser automation must include stealth scripts to avoid detection:
```python
# Always inject anti-detection when creating browser contexts
await page.add_init_script("""
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = { runtime: {} };
""")
```

### 2. Database Session Management
Use `database_manager.get_session_direct()` for direct SQLAlchemy sessions:
```python
from src.core.database_manager import database_manager
session = database_manager.get_session_direct()
try:
    # Database operations
finally:
    session.close()
```

### 3. Configuration Directory Structure
All app data goes to `~/.xhs_system/`:
- `settings.json` - Simple config (legacy)
- `config.json` - Structured config 
- `xhs_data.db` - SQLite database
- `backups/` - Database backups

### 4. Multi-User Architecture
The system supports multiple Xiaohongshu accounts with:
- User-specific proxy configurations (`ProxyConfig` model)
- Browser fingerprints (`BrowserFingerprint` model)
- Content templates per user (`ContentTemplate` model)

## Essential Workflows

### Installation & Setup
```bash
# Cross-platform installation (Windows/macOS/Linux)
./install.sh           # Linux/macOS
install.bat            # Windows
python deploy.py       # Direct Python deployment
```

### Running the Application
```bash
# Desktop GUI
python main.py

# Web interface  
cd src/web && python app.py
# Access at http://localhost:8000
```

### Database Operations
```bash
# Initialize/reset database
python init_db.py

# Database health checks are automatic on startup
# See database_manager.ensure_database_ready()
```

## Key Integration Points

### PyQt5 ↔ Playwright Integration
The desktop app runs Playwright in separate threads using `QThread`:
```python
# See src/core/write_xiaohongshu.py - VerificationCodeHandler
# Uses PyQt signals for async communication with browser automation
```

### Web ↔ Core Services
FastAPI routes delegate to core services:
- `BrowserManager` - Browser lifecycle
- `AuthManager` - Login sessions  
- `ContentManager` - Content CRUD
- `SessionManager` - State persistence

### Selector Configuration System
XHS selectors are centralized in `src/core/config.py`:
```python
# XiaohongshuConfig.selectors contains all CSS/XPath selectors
# Update selectors here when XHS UI changes
selectors = {
    "phone_input": "//input[@placeholder='手机号']",
    "login_btn": ".beer-login-btn",
    "publish_btn": ["button:has-text('发布笔记')", ".btn:text('发布笔记')"]
}
```

## Project-Specific Conventions

### File Organization
- `src/core/` - Business logic and automation
- `src/core/pages/` - PyQt5 UI pages
- `src/core/services/` - Data access layer
- `src/core/models/` - SQLAlchemy models
- `src/web/` - FastAPI application

### Error Handling Pattern
Always log to both console and file (`~/Desktop/xhsai_error.log`):
```python
import logging
log_path = os.path.expanduser('~/Desktop/xhsai_error.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG)
```

### Async Context Managers
Browser resources use async context managers for proper cleanup:
```python
async with BrowserManager() as browser_mgr:
    # Browser operations here
    # Automatic cleanup on exit
```

## Development Environment

### Required Dependencies
- **Python 3.8+** (see version checks in install scripts)
- **Playwright** for browser automation
- **PyQt5** for desktop GUI
- **FastAPI** for web interface
- **SQLAlchemy 2.0+** for data persistence

### PyInstaller Packaging
The project includes `main.spec` for creating standalone executables with embedded Playwright browsers and all dependencies.

### Testing Strategy
No formal test suite currently exists. Test manually with:
1. Database initialization (`python init_db.py`)
2. Desktop GUI (`python main.py`)
3. Web interface (`cd src/web && python app.py`)
4. XHS login/publishing workflows

## MCP Integration Considerations

### Browser Automation vs MCP Tools
The current Playwright-based automation provides direct browser control for XHS publishing workflows. MCP Link offers a higher-level framework for AI tool integration but operates at a different abstraction layer.

### Potential Integration Points
- **Tool Registration**: Expose XHS publishing as MCP tools for AI agents
- **Workflow Orchestration**: Use MCP for coordinating multi-step publishing tasks
- **Security Layer**: Add MCP's permission system on top of existing automation
- **Extension Integration**: Browser extension could provide additional XHS-specific tools

## MCP Integration Considerations

### Browser Automation vs MCP Tools
The current Playwright-based automation provides direct browser control for XHS publishing workflows. MCP Link offers a higher-level framework for AI tool integration but operates at a different abstraction layer.

### Potential Integration Points
- **Tool Registration**: Expose XHS publishing as MCP tools for AI agents
- **Workflow Orchestration**: Use MCP for coordinating multi-step publishing tasks
- **Security Layer**: Add MCP's permission system on top of existing automation
- **Extension Integration**: Browser extension could provide additional XHS-specific tools

### Recommended Approach
Keep Playwright for core automation while considering MCP Link for:
- AI-driven content generation workflows
- Multi-tool coordination (publishing + related tasks)
- Enhanced user permission controls
- Future AI agent integrations

## Overtime Reduction Solutions

### Smart Batch Publisher (`src/core/smart_batch_publisher.py`)
**Purpose**: Eliminates manual monitoring and waiting during publishing
- **Concurrent Processing**: Handles multiple publish tasks simultaneously (configurable limit)
- **Automatic Retry**: Built-in retry logic with exponential backoff
- **Scheduled Publishing**: Queue tasks for future execution
- **Progress Tracking**: Real-time status updates without manual checking

### AI Content Generator (`src/core/ai_content_generator.py`)
**Purpose**: Reduces content creation time from hours to minutes
- **Template-Based Generation**: Pre-built templates for different content types (lifestyle, beauty, food, etc.)
- **Batch Content Creation**: Generate multiple pieces of content at once
- **Content Optimization**: AI-powered content improvement
- **Image Keyword Generation**: Automatic image search term suggestions

### Smart Monitor (`src/core/smart_monitor.py`)
**Purpose**: Provides real-time system visibility without constant checking
- **Live Dashboard**: Real-time metrics and task status
- **Automated Alerts**: Proactive notifications for issues
- **Performance Analytics**: Success rates, average publish times, failure analysis
- **Historical Reporting**: Productivity reports and trend analysis

### Smart Retry System (`src/core/smart_retry.py`)
**Purpose**: Handles failures automatically, reducing manual intervention
- **Multiple Retry Strategies**: Immediate, linear, exponential, and random backoff
- **Error Pattern Recognition**: Learns from common failure patterns
- **Automatic Recovery**: Browser restart, proxy switching, network recovery
- **Failure Analytics**: Tracks retry success rates and common issues

### Overtime Reduction Controller (`src/core/overtime_reduction_controller.py`)
**Purpose**: Unified control system for all overtime reduction features
- **One-Click Smart Publishing**: Generate content + publish automatically
- **System Health Monitoring**: Automatic component recovery
- **Productivity Metrics**: Quantified time savings and efficiency gains
- **Maintenance Automation**: Self-healing and optimization

### Usage Examples

#### Quick Content Generation + Publishing
```python
from src.core.overtime_reduction_controller import quick_publish

# 一键生成并发布5篇关于"健康饮食"的内容
task_id = await quick_publish("健康饮食", count=5)
```

#### Batch Processing with Scheduling
```python
from src.core.smart_batch_publisher import create_batch_task
from datetime import datetime, timedelta

# 创建定时批量发布任务
schedule_time = datetime.now() + timedelta(hours=2)
task_id = create_batch_task(
    user_id=1,
    contents=my_content_list,
    schedule_time=schedule_time
)
```

#### Monitor System Performance
```python
from src.core.overtime_reduction_controller import get_productivity_report

# 查看本周生产力报告
report = get_productivity_report(days=7)
print(f"自动发布 {report['auto_published_count']} 篇")
print(f"节省时间 {report['estimated_saved_time_hours']} 小时")
```

### Expected Time Savings
- **Content Creation**: 2-3 hours → 15 minutes (85% reduction)
- **Publishing Tasks**: Manual monitoring → Automated (90% reduction)
- **Error Recovery**: Manual fixes → Auto-recovery (95% reduction)
- **Batch Operations**: Sequential → Concurrent (60% reduction)

### Integration with Existing Code
All overtime reduction components are designed to work alongside existing code without breaking changes. They enhance rather than replace current functionality.