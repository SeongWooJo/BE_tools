import grpc
import gRPC.example_pb2 as pb2
import gRPC.example_pb2_grpc as pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = pb2_grpc.DataServiceStub(channel)
        
        # 데이터 생성
        request = pb2.DataRequest(
            # 1. Scalar: 일반 할당
            id=101,
            name="SeongWoo",
            value=99.9,
            active=True,
            
            # 2. Enum: 정의된 상수 사용
            current_status=pb2.DataRequest.COMPLETED
        )

        # 3. Repeated: .extend() 또는 .append() 사용 (직접 할당 불가)
        request.tags.extend(["python", "grpc", "docker"])
        
        # 4. Map: 딕셔너리처럼 값 추가
        request.metadata["version"] = "1.0.0"
        request.metadata["env"] = "dev"

        # 요청 전송
        response = stub.SendData(request)
        print(f"[Result] {response.message} (Success: {response.success})")

if __name__ == '__main__':
    run()