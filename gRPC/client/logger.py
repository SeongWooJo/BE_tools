import logging
import os

# 2. 로거 초기화 (기존 로거가 있으면 핸들러를 다 날려버림)
logger_name = "gRPC_Client"
logger = logging.getLogger(logger_name)
if logger.hasHandlers():
    logger.handlers.clear()

logger.setLevel(logging.INFO)

# 3. 파일 핸들러 설정
fh = logging.FileHandler("./gRPC/client_log.txt", mode='a', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# 4. [중요] LoggerAdapter 사용
# 이렇게 감싸면 .info(msg, rpc=method)라고 써도 TypeError가 안 납니다.
class GrpcAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        # extra에 담긴 커스텀 인자들을 메시지에 합쳐버림
        extra = kwargs.get("extra", {})
        details = ", ".join([f"{k}={v}" for k, v in extra.items()])
        return f"{msg} | {details}" if details else msg, kwargs

# 실제 인터셉터에서 사용할 로거 객체
grpc_logger = GrpcAdapter(logger, {})