import sys
sys.path.append('../python')
import numpy as np
import pytest
import TransFTrain as train
from TransFTrain import backend_ndarray as nd


_DEVICES = [nd.cpu(), pytest.param(nd.cuda(), 
    marks=pytest.mark.skipif(not nd.cuda().enabled(), reason="No GPU"))]


def compare_strides(a_np, a_nd):
    size = a_np.itemsize
    assert tuple([x // size for x in a_np.strides]) == a_nd.strides


def check_same_memory(original, view):
    assert original._handle.ptr() == view._handle.ptr()


reduce_params = [
    {"dims": (10,), "axis": 0},
    {"dims": (4, 5, 6), "axis": 0},
    {"dims": (4, 5, 6), "axis": 1},
    {"dims": (4, 5, 6), "axis": 2}
]
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
@pytest.mark.parametrize("params", reduce_params)
def test_reduce_sum(params, device):
    dims, axis = params['dims'], params['axis']
    _A = np.random.randn(*dims)
    A = nd.array(_A, device=device)   
    np.testing.assert_allclose(_A.sum(axis=axis, keepdims=True), A.sum(axis=axis).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
@pytest.mark.parametrize("params", reduce_params)
def test_reduce_max(params, device):
    dims, axis = params['dims'], params['axis']
    _A = np.random.randn(*dims)
    A = nd.array(_A, device=device)   
    np.testing.assert_allclose(_A.max(axis=axis, keepdims=True), A.max(axis=axis).numpy(), atol=1e-5, rtol=1e-5)


""" For converting slice notation to slice objects to make some proceeding tests easier to read """
class _ShapeAndSlices(nd.NDArray):
    def __getitem__(self, idxs):
        idxs = tuple([self.process_slice(s, i) if isinstance(s, slice) else slice(s, s + 1, 1)
                for i, s in enumerate(idxs)])
        return self.shape, idxs


ShapeAndSlices = lambda *shape: _ShapeAndSlices(np.ones(shape))

matmul_tiled_shapes = [(1, 1, 1), (2, 2, 3), (1, 2, 1), (3, 3, 3)]
@pytest.mark.parametrize("m,n,p", matmul_tiled_shapes)
def test_matmul_tiled(m, n, p):
    device = nd.cpu()
    assert hasattr(device, "matmul_tiled")
    t = device.__tile_size__
    A = nd.array(np.random.randn(m, n, t, t), device=nd.cpu())
    B = nd.array(np.random.randn(n, p, t, t), device=nd.cpu())
    C = nd.NDArray.make((m, p, t, t), device=nd.cpu())
    device.matmul_tiled(A._handle, B._handle, C._handle, m*t, n*t, p*t)

    lhs = A.numpy().transpose(0, 2, 1, 3).flatten().reshape(m*t, n*t) \
        @ B.numpy().transpose(0, 2, 1, 3).flatten().reshape(n*t, p*t)
    rhs = C.numpy().transpose(0, 2, 1, 3).flatten().reshape(m*t, p*t)

    np.testing.assert_allclose(lhs, rhs, atol=1e-5, rtol=1e-5)


OPS = {
    "multiply": lambda a, b: a * b,
    "divide": lambda a, b: a / b,
    "add": lambda a, b: a + b,
    "subtract": lambda a, b: a - b,
    "equal": lambda a, b: a == b,
    "greater_than": lambda a, b: a >= b
}
OP_FNS = [OPS[k] for k in OPS]
OP_NAMES = [k for k in OPS]

ewise_shapes = [(1, 1, 1), (4, 5, 6)]
@pytest.mark.parametrize("fn", OP_FNS, ids=OP_NAMES)
@pytest.mark.parametrize("shape", ewise_shapes)
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_ewise_fn(fn, shape, device):
    _A = np.random.randn(*shape)
    _B = np.random.randn(*shape)
    A = nd.array(_A, device=device)
    B = nd.array(_B, device=device)
    np.testing.assert_allclose(fn(_A, _B), fn(A, B).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("shape", ewise_shapes)
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_ewise_max(shape, device):
    _A = np.random.randn(*shape)
    _B = np.random.randn(*shape)
    A = nd.array(_A, device=device)
    B = nd.array(_B, device=device)
    np.testing.assert_allclose(np.maximum(_A, _B), A.maximum(B).numpy(), atol=1e-5, rtol=1e-5)


permute_params = [
    {"dims": (4, 5, 6), "axes": (0, 1, 2)},
    {"dims": (4, 5, 6), "axes": (1, 0, 2)},
    {"dims": (4, 5, 6), "axes": (2, 1, 0)},
]
@pytest.mark.parametrize("params", permute_params)
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_permute(device, params):
    dims = params['dims']
    axes = params['axes']
    _A = np.random.randn(*dims)
    A = nd.array(_A, device=device)
    lhs = np.transpose(_A, axes=axes)
    rhs = A.permute(axes)
    np.testing.assert_allclose(lhs, rhs.numpy(), atol=1e-5, rtol=1e-5)
    compare_strides(lhs, rhs)
    check_same_memory(A, rhs)


reshape_params = [
    {"shape": (8, 16), "new_shape": (2, 4, 16)},
    {"shape": (8, 16), "new_shape": (8, 4, 2, 2)},
]
@pytest.mark.parametrize("params", reshape_params)
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_reshape(device, params):
    shape = params['shape']
    new_shape = params['new_shape']
    _A = np.random.randn(*shape)
    A = nd.array(_A, device=device)
    lhs = _A.reshape(*new_shape)
    rhs = A.reshape(new_shape)
    np.testing.assert_allclose(lhs, rhs.numpy(), atol=1e-5, rtol=1e-5)
    compare_strides(lhs, rhs)
    check_same_memory(A, rhs)


getitem_params = [
    {"shape": (8, 16), "fn": lambda X: X[3:4, 3:4]},
    {"shape": (8, 16), "fn": lambda X: X[1:2, 1:3]},
    {"shape": (8, 16), "fn": lambda X: X[3:4, 1:4]},
    {"shape": (8, 16), "fn": lambda X: X[1:4, 3:4]},
]
@pytest.mark.parametrize("params", getitem_params)
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_getitem(device, params):
    shape = params['shape']
    fn = params['fn']
    _A = np.random.randn(5, 5)
    A = nd.array(_A, device=device)
    lhs = fn(_A)
    rhs = fn(A)
    np.testing.assert_allclose(lhs, rhs.numpy(), atol=1e-5, rtol=1e-5)
    compare_strides(lhs, rhs)
    check_same_memory(A, rhs)


broadcast_params = [
    {"from_shape": (1, 3, 4), "to_shape": (6, 3, 4)},
]
@pytest.mark.parametrize("params", broadcast_params)
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_broadcast_to(device, params):
    from_shape, to_shape = params['from_shape'], params['to_shape']
    _A = np.random.randn(*from_shape)
    A = nd.array(_A, device=device)
    lhs = np.broadcast_to(_A, shape=to_shape)
    rhs = A.broadcast_to(to_shape)
    np.testing.assert_allclose(lhs, rhs.numpy(), atol=1e-5, rtol=1e-5)
    compare_strides(lhs, rhs)
    check_same_memory(A, rhs)


matmul_dims = [(16, 16, 16), 
    (8, 8, 8), 
    (1, 2, 3), 
    (3, 4, 5), 
    (5, 4, 3), 
    (64, 64, 64), 
    (72, 72, 72), 
    (72, 73, 74), 
    (74, 73, 72), 
    (128, 128, 128)]
@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
@pytest.mark.parametrize("m,n,p", matmul_dims)
def test_matmul(m, n, p, device):
    _A = np.random.randn(m, n)
    _B = np.random.randn(n, p)
    A = nd.array(_A, device=device)
    B = nd.array(_B, device=device)
    np.testing.assert_allclose((A @ B).numpy(), _A @ _B, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_scalar_mul(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    np.testing.assert_allclose(A * 5., (B * 5.).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_scalar_div(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    np.testing.assert_allclose(A / 5., (B / 5.).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_scalar_power(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    np.testing.assert_allclose(np.power(A, 5.), (B**5.).numpy(), atol=1e-5, rtol=1e-5)
    np.testing.assert_allclose(np.power(A, 0.5), (B**0.5).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_scalar_maximum(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    C = (np.max(A) + 1.).item()
    np.testing.assert_allclose(np.maximum(A, C), (B.maximum(C)).numpy(), atol=1e-5, rtol=1e-5)
    C = (np.max(A) - 1.).item()
    np.testing.assert_allclose(np.maximum(A, C), (B.maximum(C)).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_scalar_eq(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    C = A[0,1].item()
    np.testing.assert_allclose(A == C, (B == C).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_scalar_ge(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    C = A[0, 1].item()
    np.testing.assert_allclose(A >= C, (B >= C).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_ewise_log(device):
    A = np.abs(np.random.randn(5, 5))
    B = nd.array(A, device=device)
    np.testing.assert_allclose(np.log(A), (B.log()).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_ewise_exp(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    np.testing.assert_allclose(np.exp(A), (B.exp()).numpy(), atol=1e-5, rtol=1e-5)


@pytest.mark.parametrize("device", _DEVICES, ids=["cpu", "cuda"])
def test_ewise_tanh(device):
    A = np.random.randn(5, 5)
    B = nd.array(A, device=device)
    np.testing.assert_allclose(np.tanh(A), (B.tanh()).numpy(), atol=1e-5, rtol=1e-5)


######################    |    ######################
###################### MUGRADE ######################
######################    v    ######################

def Prepare(A):
    return (A.numpy().flatten()[:128], A.strides, A.shape)


def Rand(*shape, device=nd.cpu(), entropy=1):
    np.random.seed(np.prod(shape) * len(shape) * entropy)
    _A = np.random.randint(low=1, high=100, size=shape)
    return nd.array(_A, device=device)


def RandC(*shape, entropy=1):
    if nd.cuda().enabled():
        return Rand(*shape, device=nd.cuda(), entropy=2)
    else:
        raise NotImplementedError("You need a GPU to run these tests.")


if __name__ == "__main__":
    print("You have to run the tests with pytest due to parameterization.")