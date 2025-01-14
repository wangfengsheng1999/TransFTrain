import unittest

import sys
sys.path.append('./python')
# 你需要在.vscode里面添加extra地址 才能找到
import TransFTrain as train
import TransFTrain.backend_ndarray as nd
import numpy as np


GENERAL_SHAPES = [(1, 1, 1), (4, 5, 6)]


class TestEwiseDiv(unittest.TestCase):
    def test_case1_cpu(self):
        shape = (1, 1, 1)
        fn = lambda a, b: a / b
        _A = np.random.randn(*shape)
        _B = np.random.randn(*shape)
        A = nd.array(_A, device= nd.cpu())
        B = nd.array(_B, device=nd.cpu())
        np.testing.assert_allclose(fn(_A, _B), fn(A, B).numpy(), atol=1e-5, rtol=1e-5)


    @unittest.skipIf(not train.cuda().enabled(), "NO GPU")
    def test_case1_cuda(self):
        shape = (1, 1, 1)
        fn = lambda a, b: a / b
        _A = np.random.randn(*shape)
        _B = np.random.randn(*shape)
        A = nd.array(_A, device= train.cuda())
        B = nd.array(_B, device=train.cuda())
        np.testing.assert_allclose(fn(_A, _B), fn(A, B).numpy(), atol=1e-5, rtol=1e-5)

    def test_case2_cpu(self):
        shape = (4, 5, 6)
        fn = lambda a, b: a / b
        _A = np.random.randn(*shape)
        _B = np.random.randn(*shape)
        A = nd.array(_A, device= nd.cpu())
        B = nd.array(_B, device=nd.cpu())
        np.testing.assert_allclose(fn(_A, _B), fn(A, B).numpy(), atol=1e-5, rtol=1e-5)


    @unittest.skipIf(not train.cuda().enabled(), "NO GPU")
    def test_case2_cuda(self):
        shape = (4, 5, 6)
        fn = lambda a, b: a / b
        _A = np.random.randn(*shape)
        _B = np.random.randn(*shape)
        A = nd.array(_A, device= train.cuda())
        B = nd.array(_B, device=train.cuda())
        np.testing.assert_allclose(fn(_A, _B), fn(A, B).numpy(), atol=1e-5, rtol=1e-5)


    def test_ewise_fn_cpu(fn, shape, device):
        device = train.cpu()
        fn = lambda a, b: a / b
        _A = np.random.randn(*shape).astype(np.float32)
        _B = np.random.randn(*shape).astype(np.float32)
        A = train.Tensor(nd.array(_A), device=device)
        B = train.Tensor(nd.array(_B), device=device)
        np.testing.assert_allclose(fn(_A, _B), fn(A, B).numpy(), atol=1e-5, rtol=1e-5)

    @unittest.skipIf(not train.cuda().enabled(), "NO GPU")
    def test_ewise_fn_cuda(fn, shape, device):
        device = train.cuda()
        fn = lambda a, b: a / b
        for shape in GENERAL_SHAPES:
            _A = np.random.randn(*shape).astype(np.float32)
            _B = np.random.randn(*shape).astype(np.float32)
            A = train.Tensor(nd.array(_A), device=device)
            B = train.Tensor(nd.array(_B), device=device)
            np.testing.assert_allclose(fn(_A, _B), fn(A, B).numpy(), atol=1e-5, rtol=1e-5)

if "__main__" == __name__:
    unittest.main()
