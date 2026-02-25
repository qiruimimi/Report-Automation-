#!/usr/bin/env python3
"""
重试处理器测试

测试retry_handler模块的重试机制
"""

import pytest
import time
from src.retry_handler import RetryHandler, RetryConfig, retry


class TestRetryHandler:
    """重试处理器测试类"""

    def test_success_on_first_try(self, logger):
        """测试首次成功"""
        handler = RetryHandler(max_retries=3, base_delay=0.1, logger=logger)

        def success_func():
            return "success"

        result = handler.retry(success_func)
        assert result == "success"

    def test_retry_then_success(self, logger):
        """测试重试后成功"""
        handler = RetryHandler(max_retries=3, base_delay=0.1, logger=logger)

        attempt_count = {'count': 0}

        def fail_twice_func():
            attempt_count['count'] += 1
            if attempt_count['count'] < 3:
                raise ValueError(f"Attempt {attempt_count['count']}")
            return "success"

        result = handler.retry(fail_twice_func)
        assert result == "success"
        assert attempt_count['count'] == 3

    def test_max_retries_exceeded(self, logger):
        """测试超过最大重试次数"""
        handler = RetryHandler(max_retries=2, base_delay=0.1, logger=logger)

        attempt_count = {'count': 0}

        def always_fail_func():
            attempt_count['count'] += 1
            raise RuntimeError(f"Always fail at attempt {attempt_count['count']}")

        with pytest.raises(RuntimeError):
            handler.retry(always_fail_func)

        assert attempt_count['count'] == 3  # 初始 + 2次重试

    def test_delay_calculation(self):
        """测试延迟计算"""
        handler = RetryHandler(
            max_retries=5,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0
        )

        # 第1次重试: base_delay * 2^0 = 1.0
        assert handler._calculate_delay(2) == 1.0

        # 第2次重试: base_delay * 2^1 = 2.0
        assert handler._calculate_delay(3) == 2.0

        # 第3次重试: base_delay * 2^2 = 4.0
        assert handler._calculate_delay(4) == 4.0

        # 第4次重试: base_delay * 2^3 = 8.0
        assert handler._calculate_delay(5) == 8.0

    def test_max_delay_cap(self):
        """测试最大延迟限制"""
        handler = RetryHandler(
            max_retries=5,
            base_delay=1.0,
            max_delay=5.0,
            backoff_factor=2.0
        )

        # 超过max_delay时应该被限制
        assert handler._calculate_delay(5) == 5.0
        assert handler._calculate_delay(10) == 5.0

    def test_decorator_success(self):
        """测试装饰器成功案例"""
        @retry(max_retries=2, base_delay=0.05)
        def decorated_func(x):
            return x * 2

        result = decorated_func(5)
        assert result == 10

    def test_decorator_retry(self):
        """测试装饰器重试"""
        attempt_count = {'count': 0}

        @retry(max_retries=2, base_delay=0.05)
        def fail_once_func():
            attempt_count['count'] += 1
            if attempt_count['count'] == 1:
                raise ValueError("Fail once")
            return "success"

        result = fail_once_func()
        assert result == "success"
        assert attempt_count['count'] == 2

    def test_specific_exception_retry(self, logger):
        """测试特定异常重试"""
        handler = RetryHandler(
            max_retries=2,
            base_delay=0.1,
            retryable_exceptions=(ValueError,),
            logger=logger
        )

        attempt_count = {'count': 0}

        def raise_value_error():
            attempt_count['count'] += 1
            if attempt_count['count'] < 3:
                raise ValueError(f"ValueError {attempt_count['count']}")
            return "success"

        result = handler.retry(raise_value_error)
        assert result == "success"

    def test_non_retryable_exception(self, logger):
        """测试不可重试异常"""
        handler = RetryHandler(
            max_retries=2,
            base_delay=0.1,
            retryable_exceptions=(ValueError,),
            logger=logger
        )

        def raise_runtime_error():
            raise RuntimeError("Not retryable")

        with pytest.raises(RuntimeError):
            handler.retry(raise_runtime_error)


class TestRetryConfig:
    """重试配置测试类"""

    def test_create_network_config(self, logger):
        """测试创建网络配置"""
        handler = RetryConfig.create_handler(
            RetryConfig.NETWORK_CONFIG,
            logger
        )

        assert handler.max_retries == 5
        assert handler.base_delay == 0.5
        assert handler.max_delay == 30.0
        assert handler.backoff_factor == 2.0

    def test_create_database_config(self, logger):
        """测试创建数据库配置"""
        handler = RetryConfig.create_handler(
            RetryConfig.DATABASE_CONFIG,
            logger
        )

        assert handler.max_retries == 3
        assert handler.base_delay == 1.0
        assert handler.max_delay == 10.0

    def test_create_file_config(self, logger):
        """测试创建文件配置"""
        handler = RetryConfig.create_handler(
            RetryConfig.FILE_CONFIG,
            logger
        )

        assert handler.max_retries == 2
        assert handler.base_delay == 2.0
        assert handler.max_delay == 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
