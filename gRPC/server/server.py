
import grpc
from concurrent import futures
import gRPC.example_pb2 as pb2
import gRPC.example_pb2_grpc as pb2_grpc
import logging

# 1. 로깅 설정 (서버 로그를 'server_log.txt'에 저장)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("./gRPC/server_log.txt", encoding='utf-8'), # 파일 저장
        logging.StreamHandler()                                  # 콘솔 출력(선택)
    ]
)
logger = logging.getLogger("gRPC_Server")

class DataServicer(pb2_grpc.DataServiceServicer):
    def SendData(self, request, context):
        logger.info("--- New Request Received ---")
        
        # 1. Scalar 읽기
        logger.info(f"ID: {request.id}, Name: {request.name}")
        
        # 2. Enum 읽기
        status_name = pb2.DataRequest.Status.Name(request.current_status)
        logger.info(f"Status: {status_name} ({request.current_status})")
        
        # 3. Repeated 읽기
        logger.info(f"Tags: {list(request.tags)}")
        
        # 4. Map 읽기
        for key, val in request.metadata.items():
            logger.info(f"Metadata: {key} -> {val}")

        logger.info("--- Request Processed Successfully ---")
        return pb2.DataResponse(message="Success!", success=True)


class Server():
    def __init__(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        pb2_grpc.add_DataServiceServicer_to_server(DataServicer(), self.server)
        self.server.add_insecure_port('[::]:50051')
    
    def start_server(self):
        self.server.start()
        print("[*] Server started on port 50051")
        print("See log in server_log.txt")

    def stop_server(self):
        self.server.stop(grace=0)
        print("[*] gRPC Server stopped.")
