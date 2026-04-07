"""
Module de conditions logiques et temporelles pour la robotique.

Ce module fournit des classes abstraites et concrètes permettant de définir, combiner et évaluer des conditions booléennes, temporelles ou liées à des états surveillés. Il est conçu pour être utilisé dans des systèmes de contrôle, d'automatisation ou de robotique nécessitant des conditions complexes et composables.

Exemples d'utilisation :
    >>> c = AlwaysTrueCondition()
    >>> bool(c)
    True
    >>> c2 = ValueCondition(5, 5)
    >>> bool(c2)
    True
    >>> allc = AllConditions([c, c2])
    >>> bool(allc)
    True
"""
from typing import Self, override, Any
from abc import ABC, abstractmethod
from elapsed_timer import ElapsedTimer
from type_utilities import GenericGenerator, OptionalOneOrMany, OneOrMany

#Commande pour corriger le fichier:
#mypy --strict --check-untyped-defs condition.py

class Condition(ABC):
    """Classe abstraite pour des conditions évaluables en bool.

    Cette classe fournit un cadre pour créer des conditions pouvant être inversées.
    Les sous-classes doivent implémenter la méthode _compare pour définir la logique
    de la condition.
    """

    def __init__(self:Self, invert:bool = False):
        """Initialise la condition avec un indicateur d'inversion optionnel.

        Args:
            invert: Si True, le résultat de la condition est inversé.
        """
        self.__invert:bool = invert

    def __bool__(self:Self) -> bool:
        """Évalue la condition en une valeur booléenne.

        Returns:
            Le résultat booléen de la condition, potentiellement inversé.
        """
        return self._compare() != self.invert

    @property
    def invert(self:Self) -> bool:
        """Obtient l'indicateur d'inversion.

        Returns:
            True si la condition est inversée, False sinon.
        """
        return self.__invert
    
    @invert.setter
    def invert(self:Self, value:bool) -> None:
        """Définit l'indicateur d'inversion.

        Args:
            value: La nouvelle valeur d'inversion.

        Raises:
            ValueError: Si la valeur n'est pas un booléen.
        """
        if not isinstance(value, bool):
            raise ValueError("Value must be a bool")
        self.__invert = bool(value)
    
    @abstractmethod
    def _compare(self:Self)-> bool:
        """Méthode abstraite pour comparer la condition.

        Returns:
            Le résultat booléen brut de la condition avant inversion.
        """
        pass

    def toogle_invert(self:Self) -> None:
        """Inverse l'indicateur d'inversion."""
        self.__invert = not self.__invert

class AlwaysTrueCondition(Condition):
    """Condition qui est toujours vraie.

    Utile comme valeur par défaut ou pour les tests.

    Exemples:
        >>> bool(AlwaysTrueCondition())
        True
        >>> bool(AlwaysTrueCondition(invert=True))
        False
    """

    def __init__(self:Self, invert:bool = False):
        """Initialise la condition toujours vraie.

        Args:
            invert: Si True, la condition est inversée (toujours False).
        """
        super().__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        """
        Compare la condition, retourne toujours True.

        Returns:
            bool: Toujours True.
        """
        return True
    
class AlwaysFalseCondition(Condition):
    """Condition qui est toujours fausse.

    Utile comme valeur par défaut ou pour les tests.

    Exemples:
        >>> bool(AlwaysFalseCondition())
        False
        >>> bool(AlwaysFalseCondition(invert=True))
        True
    """

    def __init__(self:Self, invert:bool = False):
        """Initialise la condition toujours fausse.

        Args:
            invert: Si True, la condition est inversée (toujours True).
        """
        super().__init__(invert)

    @override
    def _compare(self:Self)-> bool:
        """
        Compare la condition, retourne toujours False.

        Returns:
            bool: Toujours False.
        """
        return False
    
class ElapsedTimerCondition(Condition):
    """Condition qui devient vraie après une durée écoulée spécifiée.

    Utilise un ElapsedTimer pour accumuler le temps. Cette condition passe
    à True lorsque le temps écoulé est supérieur ou égal à la durée.

    Note: les tests basés sur le temps ne sont pas fiables comme doctests.
    """

    def __init__(self:Self, duration:float, invert:bool = False):
        """Initialise la condition de temporisation.

        Args:
            duration: Durée en secondes après laquelle la condition devient True.
            invert: Si True, la condition est inversée.
        """
        super().__init__(invert)
        self.__duration:float = float(duration)
        self.__elapsed_timer:ElapsedTimer = ElapsedTimer(ElapsedTimer.Mode.ACCUMULATED)

    @property
    def duration(self:Self) -> float:
        """Obtient la durée.

        Returns:
            La durée en secondes.
        """
        return self.__duration
    
    @duration.setter
    def duration(self:Self, value:float) -> None:
        """Définit la durée.

        Args:
            value: La nouvelle durée en secondes.
        """
        self.__duration = float(value)
    
    @override
    def _compare(self:Self)-> bool:
        """
        Compare la condition selon le temps écoulé.

        Returns:
            bool: True si le temps écoulé est supérieur ou égal à la durée.
        """
        return self.__elapsed_timer.elapsed >= self.__duration

    def reset(self:Self) -> None:
        """Réinitialise le elapsed timer."""
        self.__elapsed_timer.reset()

class AbstractValueCondition[T](Condition):
    """Classe de base pour les conditions comparant à une valeur attendue.

    Les sous-classes doivent définir comment obtenir la valeur réelle pour la comparaison.
    """

    def __init__(self:Self, expected_value: T , invert:bool = False):
        """Initialise la condition avec la valeur attendue.

        Args:
            expected_value: La valeur à comparer.
            invert: Si True, la condition est inversée.
        """
        super().__init__(invert)
        self._expected_value:T = expected_value

    @property
    def expected_value(self:Self) -> T:
        """Obtient la valeur attendue.

        Returns:
            La valeur attendue.
        """
        return self._expected_value
    
    @expected_value.setter
    def expected_value(self:Self, value:T) -> None:
        """Définit la valeur attendue.

        Args:
            value: La nouvelle valeur attendue.
        """
        self._expected_value = value
    
class ReaderCondition[T](AbstractValueCondition[T]):
    """Condition qui compare une valeur attendue à une valeur lue via un callable.

    La valeur est obtenue en appelant value_reader().

    Exemples:
        >>> reader = ReaderCondition(5, lambda: 5)
        >>> bool(reader)
        True
        >>> reader.value_reader = lambda: 3
        >>> bool(reader)
        False
    """

    def __init__(self:Self, expected_value : T, value_reader:GenericGenerator[T], invert:bool = False):
        """Initialise la ReaderCondition.

        Args:
            expected_value: La valeur attendue.
            value_reader: Un callable qui retourne la valeur réelle.
            invert: Si True, la condition est inversée.
        """
        super().__init__(expected_value, invert)
        self._value_reader:GenericGenerator[T] = value_reader

    @property
    def value_reader(self:Self) -> GenericGenerator[T]:
        """Obtient le callable de lecture de valeur.

        Returns:
            Le callable qui fournit la valeur réelle.
        """
        return self._value_reader
    
    @value_reader.setter
    def value_reader(self:Self, value:GenericGenerator[T]) -> None:
        """Définit le callable de lecture de valeur.

        Args:
            value: Le nouveau callable.

        Raises:
            ValueError: Si la valeur n'est pas callable.
        """
        if not callable(value):
            raise ValueError("The value_reader must be a Callable")
        self._value_reader = value
    
    @override
    def _compare(self:Self)-> bool:
        """
        Compare la valeur attendue à la valeur lue.

        Returns:
            bool: True si les valeurs sont égales.
        """
        return bool(self.expected_value == self.value_reader())
    
class ValueCondition[T](AbstractValueCondition[T]):
    """Condition qui compare une valeur attendue à une valeur réelle statique.

    Exemples:
        >>> vc = ValueCondition(10, 10)
        >>> bool(vc)
        True
        >>> vc.actual_value = 5
        >>> bool(vc)
        False
    """

    def __init__(self:Self, expected_value : T, actual_value:T, invert:bool = False):
        """Initialise la ValueCondition.

        Args:
            expected_value: La valeur attendue.
            actual_value: La valeur réelle statique.
            invert: Si True, la condition est inversée.
        """
        super().__init__(expected_value, invert)
        self._actual_value:T = actual_value

    @property
    def actual_value(self:Self) -> T:
        """Obtient la valeur réelle.

        Returns:
            La valeur réelle.
        """
        return self._actual_value
    
    @actual_value.setter
    def actual_value(self:Self, value:T) -> None:
        """Définit la valeur réelle.

        Args:
            value: La nouvelle valeur réelle.
        """
        self._actual_value = value
    
    @override
    def _compare(self:Self)-> bool:
        """
        Compare la valeur attendue à la valeur réelle.

        Returns:
            bool: True si les valeurs sont égales.
        """
        return bool(self.expected_value == self.actual_value)

class ManyConditions(Condition):
    """Classe de base pour des conditions opérant sur plusieurs sous-conditions.

    Fournit des méthodes pour ajouter, supprimer et effacer des conditions.
    """

    def __init__(self:Self, condition : OptionalOneOrMany[Condition], invert:bool = False):
        """Initialise ManyConditions.

        Args:
            condition: Condition(s) initiale(s) à inclure.
            invert: Si True, la condition est inversée.
        """
        super().__init__(invert)
        self._condition : OptionalOneOrMany[Condition] = condition
    
    def clear_conditions(self:Self) -> None:
        """Efface toutes les conditions."""
        self._condition = None

    def add_condition(self: Self, condition: OneOrMany[Condition]) -> None:
        """Ajoute une ou plusieurs conditions.

        Args:
            condition: La condition(s) à ajouter.
        """
        if self._condition is not None:

            if isinstance(self._condition, Condition):
                conditions = [self._condition]
            else:
                conditions = list(self._condition)

            if isinstance(condition, Condition):
                conditions.append(condition)
            else:
                conditions.extend(condition)

            self._condition = conditions

    def remove_condition(self: Self, condition: OneOrMany[Condition]) -> None:
        """Supprime une ou plusieurs conditions.

        Args:
            condition: La condition(s) à supprimer.
        """
        if self._condition is not None:

            if isinstance(self._condition, Condition):
                conditions = [self._condition]
            else:
                conditions = list(self._condition)

            if isinstance(condition, Condition):
                if condition in conditions:
                    conditions.remove(condition)
            else: # iterable
                for c in condition:
                    if c in conditions:
                        conditions.remove(c)

            self._condition = conditions or None

class AllConditions(ManyConditions):
    """Condition qui est vraie seulement si toutes les sous-conditions sont vraies.

    Exemples:
        >>> a = AlwaysTrueCondition()
        >>> b = AlwaysFalseCondition()
        >>> bool(AllConditions([a, a]))
        True
        >>> bool(AllConditions([a, b]))
        False
    """

    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
        """Initialise AllConditions.

        Args:
            condition: Condition(s) initiale(s).
            invert: Si True, la condition est inversée.
        """
        super().__init__(condition, invert)

    @override
    def _compare(self:Self)-> bool:
        """
        Compare en vérifiant si toutes les conditions sont vraies.

        Returns:
            bool: True si toutes les sous-conditions sont vraies, False sinon.
        """
        if self._condition is None:
            return False
        if isinstance(self._condition, Condition):
            return self._condition._compare()
        return all(c._compare() for c in self._condition)
    
class AnyConditions(ManyConditions):
    """Condition qui est vraie si au moins une sous-condition est vraie.

    Exemples:
        >>> a = AlwaysTrueCondition()
        >>> b = AlwaysFalseCondition()
        >>> bool(AnyConditions([b, b]))
        False
        >>> bool(AnyConditions([b, a]))
        True
    """

    def __init__(self:Self, condition : OptionalOneOrMany[Condition] = None, invert:bool = False):
        """Initialise AnyConditions.

        Args:
            condition: Condition(s) initiale(s).
            invert: Si True, la condition est inversée.
        """
        super().__init__(condition, invert)

    @override
    def _compare(self:Self)-> bool:
        """
        Compare en vérifiant si au moins une condition est vraie.

        Returns:
            bool: True si au moins une sous-condition est vraie, False sinon.
        """
        if self._condition is None:
            return False
        if isinstance(self._condition, Condition):
            return self._condition._compare()
        return any(c._compare() for c in self._condition)
    
class CountConditions(ManyConditions):
    """Condition basée sur le nombre de sous-conditions qui remplissent un critère.

    Permet de vérifier un nombre exact ou au moins un certain nombre.

    Exemples:
        >>> a = AlwaysTrueCondition()
        >>> b = AlwaysFalseCondition()
        >>> bool(CountConditions(1, [b, a]))
        True
        >>> bool(CountConditions(2, [a, b], exact_bool_count=True))
        False
    """

    def __init__(self:Self, n:int, condition : OptionalOneOrMany[Condition] = None, expected_condition_value:bool = True, exact_bool_count:bool=True , invert:bool = False):
        """Initialise CountConditions.

        Args:
            n: Le nombre de conditions à vérifier.
            condition: Condition(s) initiale(s).
            expected_condition_value: La valeur bool attendue (True ou False).
            exact_bool_count: Si True, nécessite exactement n correspondances; si False, au moins n.
            invert: Si True, la condition est inversée.
        """
        super().__init__(condition, invert)
        self.__n:int = n
        self.__expected_condition_value:bool = expected_condition_value
        self.__exact_bool_count:bool = exact_bool_count

    @property
    def n(self:Self) -> int:
        """Obtient le compte n.

        Returns:
            La valeur du compte.
        """
        return self.__n
    
    @n.setter
    def n (self:Self, value : int) -> None:
        """Définit le compte n.

        Args:
            value: La nouvelle valeur de compte.
        """
        self.__n = int(value)

    @property
    def expected_condition_value(self:Self) -> bool:
        """Obtient la valeur de condition attendue.

        Returns:
            La valeur booléenne attendue.
        """
        return self.__expected_condition_value
    
    @expected_condition_value.setter
    def expected_condition_value(self:Self, value : bool) -> None:
        """Définit la valeur de condition attendue.

        Args:
            value: La nouvelle valeur attendue.

        Raises:
            ValueError: Si la valeur n'est pas un booléen.
        """
        if not isinstance(value, bool):
            raise ValueError("Value must be a bool")
        self.__expected_condition_value = bool(value)

    @property
    def exact_bool_count(self:Self) -> bool:
        """Obtient le drapeau de compte exact.

        Returns:
            True si un compte exact est requis.
        """
        return self.__exact_bool_count
    
    @exact_bool_count.setter
    def exact_bool_count(self:Self, value : bool) -> None:
        """Définit le drapeau de compte exact.

        Args:
            value: La nouvelle valeur de drapeau.

        Raises:
            ValueError: Si la valeur n'est pas un booléen.
        """
        if not isinstance(value, bool):
            raise ValueError("Value must be a bool")
        self.__exact_bool_count = value
        
    @override
    def _compare(self:Self)-> bool:
        """
        Compare selon le nombre de conditions correspondant à la valeur attendue.

        Returns:
            bool: True si le critère de comptage est respecté.
        """
        if self._condition is None:
            return False
        valid_conditions:int = 0
        if isinstance(self._condition, Condition):
            return self._condition._compare()
        else:
            for c in self._condition:
                if c._compare() == self.expected_condition_value:
                    valid_conditions += 1
        if self.exact_bool_count:
            result = True if valid_conditions == self.n else False
        else:
            result = True if valid_conditions >= self.n else False
        return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print('condition module test completed.')