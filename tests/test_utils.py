import unittest
from infrastructure.utils.format_cpf import format_cpf
from infrastructure.utils.format_cep import format_cep

class TestUtils(unittest.TestCase):
    """
    Testes unitários básicos para as funções de utilidade.
    """
    
    def test_format_cpf_valid(self):
        self.assertEqual(format_cpf("12345678901"), "123.456.789-01")
        self.assertEqual(format_cpf(12345678901), "123.456.789-01")
        
    def test_format_cpf_invalid(self):
        self.assertIsNone(format_cpf("123"))
        self.assertIsNone(format_cpf(None))
        
    def test_format_cep(self):
        self.assertEqual(format_cep("01001-000"), "01001000")
        self.assertEqual(format_cep("01.001000"), "01001000")
        self.assertIsNone(format_cep(None))

if __name__ == "__main__":
    unittest.main()
