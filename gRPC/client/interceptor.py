import time, uuid, grpc, logging, traceback
from contextvars import ContextVar
from typing import Optional
from gRPC.client.logger import grpc_logger
# Correlation ID 관리를 위한 ContextVar
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class LoggingInterceptor(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        method = client_call_details.method
        md = dict(client_call_details.metadata or [])
        cid = md.get("correlation-id") or str(uuid.uuid4())
        md["correlation-id"] = cid

        new_details = client_call_details._replace(metadata=list(md.items()))
        start = time.monotonic()

        try:
            req_bytes = len(request.SerializeToString())
        except Exception:
            req_bytes = None

        # [수정] extra를 사용하여 커스텀 인자 전달
        grpc_logger.info(
            "gRPC start!", 
            extra={"rpc": method, "correlation_id": cid, "req_bytes": req_bytes}
        )

        call = continuation(new_details, request)

        def _on_done(call_future: grpc.Future):
            latency = int((time.monotonic() - start) * 1000)
            code = call_future.code()
            details = call_future.details()

            if code == grpc.StatusCode.OK:
                try:
                    resp = call_future.result()
                    resp_bytes = len(resp.SerializeToString())
                except Exception:
                    resp_bytes = None

                # [수정] extra 사용
                grpc_logger.info(
                    "gRPC response complete",
                    extra={
                        "rpc": method, "status": "OK", "latency_ms": latency,
                        "resp_bytes": resp_bytes, "grpc_request_id": cid
                    }
                )
            else:
                tb = "".join(traceback.format_stack())
                # [수정] extra 사용
                grpc_logger.error(
                    "grpc_client_error",
                    extra={
                        "rpc": method, "status": "ERROR", "latency_ms": latency,
                        "code": code.name, "details": details, 
                        "grpc_request_id": cid, "traceback": tb
                    }
                )
        
        if isinstance(call, grpc.Future):
            call.add_done_callback(_on_done)    
        
        return call
