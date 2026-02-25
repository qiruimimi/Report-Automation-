#!/usr/bin/env python3
"""
重试机制模块

实现指数退避重试策略
"""

import time
import functools
from typing import Callable, Optional, Type, Tuple, Any
from src.logger import get_logger


class RetryHandler:
    """重试处理器 - 实现指数退避重试策略"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        logger=None
    ):
        """
        初始化重试处理器

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            backoff_factor: 退避因子
            retryable_exceptions: 可重试的异常类型
            logger: 日志记录器
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions
        self.logger = logger or get_logger('retry_handler')

    def retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行带重试的函数

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            Any: 函数返回值

        Raises:
            Exception: 重试次数耗尽后抛出最后一次异常
        """
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt > 1:
                    delay = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"重试 {func.__name__} (第 {attempt}/{self.max_retries} 次)，"
                        f"等待 {delay:.1f} 秒..."
                    )
                    time.sleep(delay)

                result = func(*args, **kwargs)
                if attempt > 1:
                    self.logger.info(
                        f"✅ {func.__name__} 重试成功 (第 {attempt} 次)"
                    )
                return result

            except self.retryable_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    self.logger.warning(
                        f"{func.__name__} 执行失败 (第 {attempt}/{self.max_retries} 次): {e}，"
                        f"将在 {delay:.1f} 秒后重试..."
                    )
                else:
                    self.logger.error(
                        f"{func.__name__} 重试 {self.max_retries} 次后仍失败: {e}"
                    )

        # 重试次数耗尽，抛出最后一次异常
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        计算延迟时间（指数退避）

        Args:
            attempt: 当前尝试次数

        Returns:
            float: 延迟时间（秒）
        """
        delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)

    def decorator(self, func: Callable) -> Callable:
        """
        重试装饰器

        Args:
            func: 要装饰的函数

        Returns:
            Callable: 装饰后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.retry(func, *args, **kwargs)
        return wrapper


class RetryConfig:
    """重试配置类 - 预定义常见重试配置"""

    # 网络请求配置 - 短延迟，多次重试
    NETWORK_CONFIG = {
        'max_retries': 5,
        'base_delay': 0.5,
        'max_delay': 30.0,
        'backoff_factor': 2.0
    }

    # 数据库查询配置 - 中等延迟
    DATABASE_CONFIG = {
        'max_retries': 3,
        'base_delay': 1.0,
        'max_delay': 10.0,
        'backoff_factor': 2.0
    }

    # 文件操作配置 - 长延迟，少次重试
    FILE_CONFIG = {
        'max_retries': 2,
        'base_delay': 2.0,
        'max_delay': 5.0,
        'backoff_factor': 1.5
    }

    @staticmethod
    def create_handler(config: dict, logger=None) -> RetryHandler:
        """
        根据配置创建重试处理器

        Args:
            config: 重试配置字典
            logger: 日志记录器

        Returns:
            RetryHandler: 重试处理器实例
        """
        return RetryHandler(
            max_retries=config.get('max_retries', 3),
            base_delay=config.get('base_delay', 1.0),
            max_delay=config.get('max_delay', 10.0),
            backoff_factor=config.get('backoff_factor', 2.0),
            logger=logger
        )


# 便捷装饰器函数
def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger=None
):
    """
    重试装饰器函数

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        backoff_factor: 退避因子
        retryable_exceptions: 可重试的异常类型
        logger: 日志记录器

    Returns:
        Callable: 装饰器函数
    """
    handler = RetryHandler(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        retryable_exceptions=retryable_exceptions,
        logger=logger
    )
    return handler.decorator


if __name__ == "__main__":
    # 测试代码
    print("测试重试处理器\n")

    handler = RetryHandler(
        max_retries=3,
        base_delay=0.5,
        max_delay=3.0
    )

    # 测试1: 成功案例
    def success_func():
        print("执行成功函数")
        return "success"

    result = handler.retry(success_func)
    print(f"结果: {result}\n")

    # 测试2: 失败后重试成功
    attempt_count = {'count': 0}

    def fail_then_success():
        attempt_count['count'] += 1
        print(f"执行失败后成功函数 (第 {attempt_count['count']} 次)")
        if attempt_count['count'] < 3:
            raise ValueError(f"模拟失败 {attempt_count['count']}")
        return "success after retry"

    result = handler.retry(fail_then_success)
    print(f"结果: {result}\n")

    # 测试3: 使用装饰器
    @retry(max_retries=2, base_delay=0.3)
    def decorated_func(x):
        print(f"执行装饰函数: {x}")
        if x == 'fail':
            raise RuntimeError("模拟失败")
        return x

    try:
        result = decorated_func('fail')
    except RuntimeError as e:
        print(f"最终失败: {e}\n")

    result = decorated_func('success')
    print(f"结果: {result}\n")
