import unittest
from time import sleep
from condition import (
    AlwaysTrueCondition,
    AlwaysFalseCondition,
    ElapsedTimerCondition,
    ReaderCondition,
    ValueCondition,
    AllConditions,
    AnyConditions,
    CountConditions,
)

class TestCondition(unittest.TestCase):

    # =========================================================================
    # 1. TESTS DE BASE ET INVERSION (Classe Condition)
    # =========================================================================
    def test_base_logic_and_inversion(self) -> None:
        """Vérifie la logique de base de True/False et l'impact de l'inversion."""
        true_c = AlwaysTrueCondition()
        false_c = AlwaysFalseCondition()
        
        self.assertTrue(bool(true_c))
        self.assertFalse(bool(false_c))
        
        # Test de l'inversion via constructeur
        self.assertFalse(bool(AlwaysTrueCondition(invert=True)))
        self.assertTrue(bool(AlwaysFalseCondition(invert=True)))

    def test_toggle_invert(self) -> None:
        """Vérifie que la méthode toogle_invert change bien l'état."""
        c = AlwaysTrueCondition()
        c.toogle_invert()
        self.assertFalse(bool(c))
        c.toogle_invert()
        self.assertTrue(bool(c))

    def test_invert_setter_validation(self) -> None:
        """Vérifie que le setter d'inversion rejette les types non-booléens."""
        c = AlwaysTrueCondition()
        with self.assertRaisesRegex(ValueError, "Value must be a bool"):
            c.invert = "True"  # type: ignore

    # =========================================================================
    # 2. CONDITIONS TEMPORELLES ET VALEURS
    # =========================================================================
    def test_elapsed_timer_condition(self) -> None:
        """Vérifie que la condition temporelle devient vraie après la durée."""
        duration = 0.05
        c = ElapsedTimerCondition(duration)
        self.assertFalse(bool(c))
        sleep(duration + 0.01)
        self.assertTrue(bool(c))
        
        c.reset()
        self.assertFalse(bool(c))

    def test_reader_condition(self) -> None:
        """Vérifie la lecture dynamique via un callable."""
        val = 10
        def mock_reader() -> int:
            return val
            
        c = ReaderCondition(expected_value=10, value_reader=mock_reader)
        self.assertTrue(bool(c))
        
        val = 5
        self.assertFalse(bool(c))

    def test_value_condition(self) -> None:
        """Vérifie la comparaison de valeurs statiques."""
        c = ValueCondition(expected_value="A", actual_value="A")
        self.assertTrue(bool(c))
        c.actual_value = "B"
        self.assertFalse(bool(c))

    # =========================================================================
    # 3. CONDITIONS MULTIPLES (Composition)
    # =========================================================================
    def test_all_conditions(self) -> None:
        """Test exhaustif de AllConditions (ET logique)."""
        # Vide
        self.assertFalse(bool(AllConditions()), "Une liste All vide devrait être False")
        
        # Succès
        c = AllConditions([AlwaysTrueCondition(), AlwaysTrueCondition()])
        self.assertTrue(bool(c))
        
        # Échec (un seul False suffit)
        c.add_condition(AlwaysFalseCondition())
        self.assertFalse(bool(c))

    def test_any_conditions(self) -> None:
        """Test exhaustif de AnyConditions (OU logique)."""
        # Vide
        self.assertFalse(bool(AnyConditions()), "Une liste Any vide devrait être False")
        
        # Succès (un seul True suffit)
        c = AnyConditions([AlwaysFalseCondition(), AlwaysTrueCondition()])
        self.assertTrue(bool(c))
        
        # Échec (que des False)
        c = AnyConditions([AlwaysFalseCondition(), AlwaysFalseCondition()])
        self.assertFalse(bool(c))

    def test_count_conditions_logic(self) -> None:
        """Test de CountConditions (Exactitude et Minimum)."""
        conds = [AlwaysTrueCondition(), AlwaysTrueCondition(), AlwaysFalseCondition()]
        
        # Cas exact (n=2 sur 3)
        c_exact = CountConditions(n=2, condition=conds, exact_bool_count=True)
        self.assertTrue(bool(c_exact))
        c_exact.n = 3
        self.assertFalse(bool(c_exact))
        
        # Cas au moins (n=1 sur 3)
        c_at_least = CountConditions(n=1, condition=conds, exact_bool_count=False)
        self.assertTrue(bool(c_at_least))

    # =========================================================================
    # 4. GESTION DE LA LISTE DE CONDITIONS (ManyConditions)
    # =========================================================================
    def test_add_remove_clear_logic(self) -> None:
        """Vérifie la manipulation de la liste interne de conditions."""
        parent = AllConditions()
        c1 = AlwaysTrueCondition()
        c2 = AlwaysTrueCondition()
        
        # Ajout unitaire
        parent.add_condition(c1)
        self.assertEqual(len(parent._condition), 1) # type: ignore
        
        # Ajout via Iterable
        parent.add_condition([c2])
        self.assertEqual(len(parent._condition), 2) # type: ignore
        
        # Suppression
        parent.remove_condition(c1)
        self.assertEqual(len(parent._condition), 1) # type: ignore
        self.assertNotIn(c1, parent._condition) # type: ignore
        
        # Clear
        parent.clear_conditions()
        self.assertEqual(len(parent._condition), 0) # type: ignore

    def test_invalid_condition_addition(self) -> None:
        """Vérifie que le système rejette les objets qui ne sont pas des Conditions."""
        parent = AllConditions()
        with self.assertRaises(ValueError):
            parent.add_condition("Not a condition") # type: ignore
        with self.assertRaises(ValueError):
            parent.add_condition([AlwaysTrueCondition(), "String"]) # type: ignore

if __name__ == "__main__":
    unittest.main()