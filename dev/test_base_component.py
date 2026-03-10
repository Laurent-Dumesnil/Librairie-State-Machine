import unittest
from typing import Any
from base_component import BaseComponent


class TestBaseComponent(unittest.TestCase):

    def setUp(self) -> None:
        # Sauvegarde des variables de classe originales
        self.original_total_instance_count: int = BaseComponent._BaseComponent__total_instance_count
        self.original_naming_padding_size: int = BaseComponent._BaseComponent__naming_padding_size
        # Réinitialisation des variables de classe pour chaque test
        BaseComponent._BaseComponent__total_instance_count = 0
        BaseComponent._BaseComponent__naming_padding_size = 4

    def tearDown(self) -> None:
        # Restauration des variables de classe originales après chaque test
        BaseComponent._BaseComponent__total_instance_count = self.original_total_instance_count
        BaseComponent._BaseComponent__naming_padding_size = self.original_naming_padding_size

    def test_default_initialization(self) -> None:
        component: BaseComponent = BaseComponent()
        self.assertIsInstance(component, BaseComponent)
        self.assertTrue(component.enabled)
        self.assertFalse(component.disabled)
        self.assertTrue(component.valid)
        self.assertIsInstance(component.name, str)

    def test_name_generation(self) -> None:
        component1: BaseComponent = BaseComponent()
        component2: BaseComponent = BaseComponent()
        expected_name1: str = 'BaseComponent0001'
        expected_name2: str = 'BaseComponent0002'
        self.assertEqual(component1.name, expected_name1)
        self.assertEqual(component2.name, expected_name2)

    def test_custom_name(self) -> None:
        component: BaseComponent = BaseComponent(name="CustomName")
        self.assertEqual(component.name, "CustomName")

    def test_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            BaseComponent(name="")

    def test_invalid_name_type(self) -> None:
        with self.assertRaises(TypeError):
            BaseComponent(name=123)  # type: ignore

    def test_invalid_enabled_type(self) -> None:
        with self.assertRaises(TypeError):
            BaseComponent(enabled="True")  # type: ignore

    def test_invalid_apply_activation_type(self) -> None:
        with self.assertRaises(TypeError):
            BaseComponent(apply_activation="False")  # type: ignore

    class TestComponent(BaseComponent):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.enabling_called: int = 0
            self.disabling_called: int = 0
            # Les dépendances sont initialisées avant l'appel du 'constructeur' de la classe de base
            super().__init__(*args, **kwargs)

        def _enabling(self) -> None:
            self.enabling_called += 1

        def _disabling(self) -> None:
            self.disabling_called += 1

    def test_enabling_disabling_methods(self) -> None:
        component: TestBaseComponent.TestComponent = self.TestComponent(enabled=False)
        self.assertEqual(component.enabling_called, 0)
        self.assertEqual(component.disabling_called, 0)
        component.enabled = True
        self.assertEqual(component.enabling_called, 1)
        self.assertEqual(component.disabling_called, 0)
        component.enabled = False
        self.assertEqual(component.enabling_called, 1)
        self.assertEqual(component.disabling_called, 1)
        component.disabled = False
        self.assertEqual(component.enabling_called, 2)
        self.assertEqual(component.disabling_called, 1)
        component.disabled = True
        self.assertEqual(component.enabling_called, 2)
        self.assertEqual(component.disabling_called, 2)

    def test_enabling_disabling_no_change(self) -> None:
        component: TestBaseComponent.TestComponent = self.TestComponent(enabled=True)
        component.enabled = True  # Pas de changement
        self.assertEqual(component.enabling_called, 0)
        self.assertEqual(component.disabling_called, 0)

    def test_disabled_property(self) -> None:
        component: BaseComponent = BaseComponent(enabled=True)
        self.assertFalse(component.disabled)
        component.disabled = True
        self.assertFalse(component.enabled)
        self.assertTrue(component.disabled)
        component.disabled = False
        self.assertTrue(component.enabled)
        self.assertFalse(component.disabled)

    def test_valid_property(self) -> None:
        component: BaseComponent = BaseComponent()
        self.assertTrue(component.valid)

    class InvalidComponent(BaseComponent):
        @property
        def valid(self) -> bool | str:
            return "Component is invalid"

    def test_invalid_component(self) -> None:
        component: TestBaseComponent.InvalidComponent = self.InvalidComponent()
        self.assertEqual(component.valid, "Component is invalid")

    def test_reset_method(self) -> None:
        component: BaseComponent = BaseComponent()
        component.reset()  # Vérifie que la méthode peut être appelée sans erreur

    def test_instance_count(self) -> None:
        self.assertEqual(BaseComponent.instance_count(), 0)
        BaseComponent()
        self.assertEqual(BaseComponent.instance_count(), 1)
        BaseComponent()
        self.assertEqual(BaseComponent.instance_count(), 2)

    def test_naming_padding_size(self) -> None:
        original_size: int = BaseComponent.naming_padding_size()
        self.assertEqual(original_size, 4)
        BaseComponent.set_naming_padding_size(6)
        self.assertEqual(BaseComponent.naming_padding_size(), 6)
        component: BaseComponent = BaseComponent()
        expected_name: str = 'BaseComponent000001'
        self.assertEqual(component.name, expected_name)
        BaseComponent.set_naming_padding_size(original_size)  # Restauration

    def test_set_naming_padding_size_invalid_type(self) -> None:
        with self.assertRaises(TypeError):
            BaseComponent.set_naming_padding_size("4")  # type: ignore

    def test_set_naming_padding_size_negative_value(self) -> None:
        with self.assertRaises(ValueError):
            BaseComponent.set_naming_padding_size(-1)

    def test_apply_activation(self) -> None:
        component: TestBaseComponent.TestComponent = self.TestComponent(enabled=True, apply_activation=True)
        self.assertEqual(component.enabling_called, 1)
        self.assertEqual(component.disabling_called, 0)
        component = self.TestComponent(enabled=False, apply_activation=True)
        self.assertEqual(component.enabling_called, 0)
        self.assertEqual(component.disabling_called, 1)

    def test_set_enabled_invalid_type(self) -> None:
        component: BaseComponent = BaseComponent()
        with self.assertRaises(TypeError):
            component.enabled = "True"  # type: ignore

    def test_set_disabled_invalid_type(self) -> None:
        component: BaseComponent = BaseComponent()
        with self.assertRaises(TypeError):
            component.disabled = 'Hello'  # type: ignore


if __name__ == '__main__':
    unittest.main()
