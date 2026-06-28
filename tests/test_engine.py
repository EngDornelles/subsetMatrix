from subsetmatrix.engine import generateMatrix


def test_generate_matrix_n3_shape():
    matrix = generateMatrix(3)
    assert matrix.shape == (6, 3)


def test_generate_matrix_n4_shape():
    matrix = generateMatrix(4)
    assert matrix.shape == (14, 4)

def test_generate_matrix_n20_shape():
    matrix = generateMatrix(20)
    assert matrix.shape == ((1 << 20) - 2, 20)
