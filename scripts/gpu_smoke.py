#!/usr/bin/env python3
"""实际GPU数值校验。需适配Jetson的torch和torchvision。"""
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    import torch
    import torchvision
    import torch.nn.functional as F
    print(json.dumps({"torch": torch.__version__, "torchvision": torchvision.__version__,
                      "cuda": torch.version.cuda, "cuda_available": torch.cuda.is_available(),
                      "compiled_arches": torch.cuda.get_arch_list()}, ensure_ascii=False))
    if not torch.cuda.is_available():
        raise SystemExit("CUDA不可用")
    print("GPU:", torch.cuda.get_device_name(0))
    torch.manual_seed(0)
    with torch.inference_mode():
        x = torch.ones((256, 256), device="cuda")
        y = x @ x
        torch.cuda.synchronize()
        assert y[0, 0].item() == 256.0
        print("矩阵乘法：PASS")
        boxes = torch.tensor([[0,0,10,10], [1,1,9,9]], dtype=torch.float32, device="cuda")
        scores = torch.tensor([0.9, 0.8], device="cuda")
        assert torchvision.ops.nms(boxes, scores, 0.5).tolist() == [0]
        print("GPU NMS：PASS")
        x = torch.randn(1,3,128,128)
        w = torch.randn(16,3,3,3) * 0.1
        ref = F.interpolate(F.silu(F.conv2d(x,w,padding=1)), scale_factor=0.5, mode="nearest")
        for dtype in (torch.float32, torch.float16):
            out = F.interpolate(F.silu(F.conv2d(x.to("cuda",dtype=dtype),
                w.to("cuda",dtype=dtype),padding=1)), scale_factor=0.5, mode="nearest")
            torch.cuda.synchronize()
            torch.testing.assert_close(out.float().cpu(),ref,rtol=0.02,atol=0.005)
            print(dtype, "卷积/激活/缩放：PASS")
    print("已测路径通过；不证明所有扩展/算子兼容。")

if __name__ == "__main__":
    main()
