import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gerador_questoes", ROOT / "backend" / "services" / "aprendizado" / "gerador_questoes.py")
GERADOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GERADOR)

class TestGeradorLocal(unittest.TestCase):
    def test_genera_quantidade_exata_para_temas_reconhecidos(self):
        casos = (("Matemática", "Porcentagem"), ("Programação", "Lógica de programação"), ("Português", "Gramática"), ("Ciências", "Corpo humano"), ("História", "Revolução Francesa"), ("Geografia", "Clima"))
        for materia, tema in casos:
            for quantidade in (5, 10, 15, 20):
                with self.subTest(materia=materia, tema=tema, quantidade=quantidade):
                    questoes, origem, aviso = GERADOR.gerar_questoes(materia, tema, "Normal", quantidade)
                    self.assertEqual(quantidade, len(questoes))
                    self.assertEqual("banco_local", origem)
                    self.assertIsNone(aviso)

    def test_questoes_tem_quatro_alternativas_e_resposta_valida(self):
        questoes, _, _ = GERADOR.gerar_questoes("Programação", "Lógica de programação", "Difícil", 20)
        for questao in questoes:
            self.assertEqual({"A", "B", "C", "D"}, set(questao["alternativas"]))
            self.assertIn(questao["alternativa_correta"], {"A", "B", "C", "D"})
            self.assertTrue(questao["enunciado"])
            self.assertTrue(questao["explicacao"])

    def test_nao_gera_perguntas_de_outra_materia_quando_tema_nao_e_reconhecido(self):
        with self.assertRaises(RuntimeError):
            GERADOR.gerar_questoes("Ciências", "Astronomia avançada", "Normal", 10)

    def test_prioriza_questoes_nao_vistas_no_mesmo_tema(self):
        primeiras, _, _ = GERADOR.gerar_questoes("Ciências", "Corpo humano", "Normal", 5)
        anteriores = [questao["enunciado"] for questao in primeiras]
        novas, _, _ = GERADOR.gerar_questoes(
            "Ciências", "Corpo humano", "Normal", 5,
            excluir_enunciados=anteriores,
        )
        self.assertEqual(5, len(novas))
        self.assertFalse(set(anteriores).intersection(q["enunciado"] for q in novas))
        self.assertEqual(5, len({q["enunciado"] for q in novas}))

if __name__ == "__main__":
    unittest.main()
