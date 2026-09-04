"""
Celery 异步任务模块

包含 Celery 实例、连通性示例任务与文档处理任务。
"""
from app.tasks.celery_app import celery_app

__all__ = ["celery_app"]
