#!/usr/bin/env python3
"""Run as normal user, in the Python environment you want to verify."""
import argparse
import sys

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['tensorrt', 'torch'])
    a = p.parse_args()
    if a.mode == 'torch':
        import torch
        print('PyTorch:', torch.__version__, 'CUDA build:', torch.version.cuda, flush=True)
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA 不可用')
        print('GPU:', torch.cuda.get_device_name(0), 'CC:', torch.cuda.get_device_capability(0), flush=True)
        x = torch.ones((128, 128), device='cuda')
        y = x @ x
        torch.cuda.synchronize()
        if y[0, 0].item() != 128:
            raise RuntimeError('GPU 矩阵计算结果异常')
        print('PASS: PyTorch CUDA 实际矩阵计算成功')
    else:
        import tensorrt as trt
        print('TensorRT:', trt.__version__, flush=True)
        logger = trt.Logger(trt.Logger.WARNING)
        builder = trt.Builder(logger)
        network = builder.create_network(0)
        x = network.add_input('input', trt.float32, (1, 1024))
        relu = network.add_activation(x, trt.ActivationType.RELU)
        network.mark_output(relu.get_output(0))
        config = builder.create_builder_config()
        serialized = builder.build_serialized_network(network, config)
        if serialized is None:
            raise RuntimeError('TensorRT 引擎构建失败')
        blob = bytes(serialized)
        runtime = trt.Runtime(logger)
        engine = runtime.deserialize_cuda_engine(blob)
        if engine is None:
            raise RuntimeError('引擎反序列化失败')
        print('PASS: 构建及加载成功，字节数:', len(blob))
        print('此检查未执行 TensorRT 推理；还需运行已验证的 YOLO engine 任务。')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('FAIL:', repr(e), file=sys.stderr)
        sys.exit(1)
