#include <cuda_runtime.h>
#include <cstdio>
#include <cmath>

__global__ void vector_add(const float *a, const float *b, float *c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}

int main() {
    int device = 0;
    cudaDeviceProp prop{};
    if (cudaGetDeviceProperties(&prop, device) != cudaSuccess) return 1;

    const int n = 1 << 20;
    const size_t bytes = n * sizeof(float);
    float *a, *b, *c;

    if (cudaMallocManaged(&a, bytes) != cudaSuccess ||
        cudaMallocManaged(&b, bytes) != cudaSuccess ||
        cudaMallocManaged(&c, bytes) != cudaSuccess) return 2;

    for (int i = 0; i < n; ++i) {
        a[i] = float(i);
        b[i] = float(i * 2);
    }

    vector_add<<<(n + 255) / 256, 256>>>(a, b, c, n);
    cudaError_t err = cudaDeviceSynchronize();
    if (err != cudaSuccess) {
        std::printf("CUDA FAIL: %s\n", cudaGetErrorString(err));
        return 3;
    }

    for (int i = 0; i < n; ++i) {
        if (std::fabs(c[i] - float(i * 3)) > 0.01f) return 4;
    }

    std::printf("CUDA COMPUTE PASS | GPU=%s | elements=%d | result=%.1f\n",
                prop.name, n, c[n - 1]);
    cudaFree(a);
    cudaFree(b);
    cudaFree(c);
    return 0;
}
