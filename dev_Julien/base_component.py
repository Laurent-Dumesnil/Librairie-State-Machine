"""
Module `base_component`

Ce module fournit une classe de base `BaseComponent` qui offre des 
fonctionnalités communes pour des composants :

 - Mécanisme de comptage des instances créées
 - Gestion du nom (avec nommage automatique si aucun n'est fourni)
 - État activé/désactivé du composant
 - Validation de la conformité du composant
 - Méthodes protégées permettant de définir un comportement spécifique lors de 
   l'activation ou de la désactivation du composant

Le module est conçu pour être utilisé comme une base pour des composants 
réutilisables qui nécessitent une gestion d'état cohérente.

Exemple simple
--------------
```python
# Création d'une instance de BaseComponent
component = BaseComponent(name="MyComponent", enabled=True)
print(component.name)  # Affiche le nom du composant, ici "MyComponent"
print(component.enabled)  # Affiche True

# Modification de l'état du composant
component.enabled = False
print(component.enabled)  # Affiche False
```
"""

from __future__ import annotations


class BaseComponent:
    """
    Classe de base offrant des fonctionnalités communes pour des composants.

    Les composants sont composés :

     - d'un mécanisme de comptage des instances créées
     - d'un nom (nommage automatique si aucun n'est donné)
     - d'un état : activé/désactivé
     - d'une validation de conformité
     - d'une réinitialisation

    Si un nom n'est pas donné, un nom unique sera généré automatiquement.
    Le format du nom généré suit ce schéma :
     - nom de la classe
     - numéro d'instance (formaté avec un remplissage de zéro)

    Le nom de la classe est défini par introspection de la classe courante, 
    permettant ainsi de connaître la classe de l'objet courant. Le numéro est 
    formaté avec un remplissage de zéro pour garantir une longueur fixe 
    (défini par la variable `naming_padding_size`). Finalement, le numéro 
    d'instance est incrémenté à chaque nouvelle instance créée.

    Les méthodes protégées `_enabling` et `_disabling` sont conçues pour être
    substituées par les classes dérivées afin de définir un comportement
    spécifique lors de l'activation ou de la désactivation du composant.

    Notes
    -----
    Cette classe est destinée à être utilisée comme une classe de base
    polymorphique pour des composants partageant cette infrastructure. 
    Les propriétés `valid`, `enabled`, `disabled` ainsi que les méthode 
    `reset`, `_enabling` et `_disabling` fournissent une interface uniforme 
    pour gérer l'état de composants similaires d'une manière cohérente.

    Exemple d'utilisation
    ---------------------
    Voici un exemple simple de création d'une instance de `BaseComponent` :

    >>> component = BaseComponent()
    >>> print(component.name)
    BaseComponent0001
    >>> component.enabled = False
    >>> print(component.enabled)
    False

    Ce code montre comment initialiser un composant, obtenir son nom
    automatiquement généré, et changer son état d'activé à désactivé.
    """

    __total_instance_count: int = 0
    __naming_padding_size: int = 4

    def __init__(self, name: str | None = None, enabled: bool = True, apply_activation: bool = False) -> None:
        """
        Initialisation
        --------------

        Initialise une nouvelle instance de `BaseComponent`.

        Paramètres `__init__`
        -----------------------
         - `name`, _optionel_
            Le nom du composant. Si `None` ou une chaîne vide, un nom par
            défaut sera généré.

         - `enabled`, _optionnel_
            Indique si le composant est activé au démarrage. Par défaut
            `True`.

         - `apply_activation`, _optionnel_
            Indique si les méthodes `_enabling` et `_disabling` doivent être
            appelées lors de l'initialisation. Par défaut `False`.
            <br>**ATTENTION** 

            - Si `apply_activation` est `True`, l'une des 
            méthodes `_enabling` ou `_disabling` sera appelée lors de 
            l'initialisation pour garantir un état cohérent. Si ces méthodes 
            sont substituées dans une classe dérivée, elles seront appelées 
            immédiatement à l'initialisation. Par conséquent, si la classe 
            dérivée possède des dépendances non encore initialisées (une 
            variable membre par exemple), cela causera systématiquement une 
            erreur. Pour ces situations, **il faut** que l'appel du 
            `__init__` de la classe parent soit appelée **après** avoir 
            initialisé les dépendances. 
            - Une autre stratégie possible est que la classe enfant définisse 
            `apply_activation` systématiquement à `False` et qu'il soit 
            impossible de la modifier via les paramètrs du `__init__` de la 
            classe dérivée.
            - Une observation technique intéressante qui dépasse le but de ce 
            projet: cette approche est impossible avec d'autres langages de 
            programmation comme Java, C# ou C++ où les méthodes 'overridables' 
            (communément appelée virtuelle ou 'virtual') ne doivent pas être 
            appelées dans le constructeur de la classe de base. La raison est 
            que l'ordre d'appel des constructeurs et strict et que le 
            constructeur parent est systématiquement appelé avant le 
            constructeur enfant sans possibilité d'en changer l'ordre. 
            On fait parfois référence à cette situation comme étant le 
            _Virtual Dispatch Trap_ ou _Premature Virtual Call_. Un dernier 
            point technique à noter est que la même situation existe pour les 
            destructeurs en C++.

        Exceptions
        ----------
         - `TypeError`
             - Si `name` n'est pas une chaîne ou `None`.
             - Si `enabled` n'est pas un booléen.
             - Si `apply_activation` n'est pas un booléen.
         - `ValueError`
             - Si `name` est une chaîne vide.
        """
        if not isinstance(name, str) and name is not None:
            raise TypeError('name must be a string or None')
        if isinstance(name, str) and len(name) == 0:
            raise ValueError('name cannot be an empty string')
        if not isinstance(enabled, bool):
            raise TypeError('enabled must be a boolean')
        if not isinstance(apply_activation, bool):
            raise TypeError('apply_activation must be a boolean')

        BaseComponent.__total_instance_count += 1
        self.__name: str = name if name else f'{self.__class__.__name__}{BaseComponent.__total_instance_count:0{BaseComponent.__naming_padding_size}d}'
        self.__enabled: bool = enabled

        if apply_activation:
            if self.__enabled:
                self._enabling()
            else:
                self._disabling()

    @staticmethod
    def instance_count() -> int:
        """
        Retourne le nombre total d'instances créées de `BaseComponent`.

        Notes
        -----
        Ne tient pas compte uniquement des composants toujours actifs mais de
        toutes les instances créées depuis le début du programme.  

        Exemple
        -------
            '''python
            count = BaseComponent.instance_count()
            '''
        """
        return BaseComponent.__total_instance_count

    @staticmethod
    def naming_padding_size() -> int:
        """
        Retourne la taille actuelle du remplissage pour le nommage automatique.

        Exemple
        -------
        >>> print(BaseComponent.naming_padding_size())
        4
        """
        return BaseComponent.__naming_padding_size

    @staticmethod
    def set_naming_padding_size(size: int) -> None:
        """
        Définit la taille du remplissage pour le nommage automatique.

        Paramètres
        ----------
         - `size`
            La nouvelle taille du remplissage.

        Exceptions
        ----------
        `TypeError`
            Si `size` n'est pas un entier.
        `ValueError`
            Si `size` est négatif.

        Exemple
        -------
        >>> BaseComponent.set_naming_padding_size(6)
        >>> print(BaseComponent.naming_padding_size())
        6
        """
        if not isinstance(size, int):
            raise TypeError('size must be an integer')
        if size < 0:
            raise ValueError('size cannot be negative')
        BaseComponent.__naming_padding_size = size

    def _enabling(self) -> None:
        """
        Méthode protégée appelée automatiquement lors de l'activation du
        composant.

        Cette méthode est destinée à être substituée dans les sous-classes pour
        définir le comportement spécifique lors d'une activation.

        Par défaut, cette méthode ne fait rien, elle est destinée au 
        polymorphisme.

        Exemple de substitution (override)
        ----------------------------------
        >>> class CustomComponent(BaseComponent):
        ...     def _enabling(self):
        ...         print("Composant activé")
        ...
        >>> component = CustomComponent()
        >>> component.enabled = True # rien puisque activé par défaut
        >>> component.enabled = False
        >>> component.enabled = True
        Composant activé
        """
        pass

    def _disabling(self) -> None:
        """
        Méthode protégée appelée automatiquement lors d'une désactivation du
        composant.

        Cette méthode est destinée à être substituée dans les sous-classes pour
        définir le comportement spécifique lors de la désactivation.

        Par défaut, cette méthode ne fait rien, elle est destinée au 
        polymorphisme.

        Exemple de substitution (override)
        ----------------------------------
        >>> class CustomComponent(BaseComponent):
        ...     def _disabling(self):
        ...         print("Composant désactivé")
        ...
        >>> component = CustomComponent()
        >>> component.enabled = False
        Composant désactivé
        """
        pass

    @property
    def valid(self) -> bool | str:
        """
        Indique si le composant est valide. _{ lecture-seule }_
        
        Retourne `True` lorsque valide et soit `False` ou une chaîne de 
        caractères expliquant la raison de l'invalidité. Si une chaîne de 
        caractères est retournée, elle doit être non vide et contenir un 
        message technique précis en anglaise.
        
        La notion de validité est liée au concept de conformité. C'est-à-dire,
        quelle indique si le composant est considéré conforme pour son
        usage. Ainsi, chaque composant peut redéfinir polymorphiquement la
        logique définissant sa validité/conformité.
        
        On peut faire un parallèle direct entre cette approche et le patron de
        conception _chaîne de responsabilité_. C'est-à-dire que la conformité 
        d'un système dépend de la conformité de tous ses composants. Ainsi, 
        dès qu'un dispositif est non conforme, le système ne l'est plus.

        Par défaut, le composant est considéré valide/conforme (retourne
        `True`).

        Exemple de vérification de validité
        -----------------------------------
        >>> component = BaseComponent()
        >>> print(component.valid)
        True
        """
        return True

    @property
    def name(self) -> str:
        """
        Le nom du composant. _{ lecture-seule }_

        Exemple
        -------
        '''python
        component = BaseComponent()
        print(component.name)
        '''
        """
        return self.__name

    @property
    def enabled(self) -> bool:
        """
        Indique si le composant est activé. _{ lecture-écriture }_

        Cette propriété est complémentaire à `disabled`.

        Seulement lorsque qu'il y a un changement d'état _effectif_,
        la méthode protégée appropriée `_enabling` ou `_disabling`
        est appelée pour assurer aux classes dérivées de gérer
        automatiquement un changement d'état adéquat.

        Exemple
        -------
        >>> component = BaseComponent()
        >>> print(component.enabled)
        True
        >>> component.enabled = False
        >>> print(component.enabled)
        False
        """
        return self.__enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError('Must be a boolean')
        
        if self.__enabled != value:
            self.__enabled = value
            if self.__enabled:
                self._enabling()
            else:
                self._disabling()

    @property
    def disabled(self) -> bool:
        """
        Indique si le composant est désactivé.  _{ lecture-écriture }_

        Cette propriété est complémentaire à `enabled` (attribut dérivé).
        
        Seulement lorsque qu'il y a un changement d'état _effectif_,
        la méthode protégée appropriée `_enabling` ou `_disabling`
        est appelée pour assurer aux classes dérivées de gérer
        automatiquement un changement d'état adéquat.

        Exemple
        -------
        >>> component = BaseComponent()
        >>> print(component.disabled)
        False
        >>> component.disabled = True
        >>> print(component.disabled)
        True
        """
        return not self.__enabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError('Must be a boolean')
        self.enabled = not value

    def reset(self) -> None:
        """
        Réinitialise le composant.

        Cette méthode réinitialise le composant dans un état initial
        cohérent. 
        
        Par défaut, cette méthode ne fait rien, elle est destinée au 
        polymorphisme.

        Exemple de réinitialisation
        ---------------------------
        >>> component = BaseComponent()
        >>> component.reset()
        """
        pass


__pdoc__ = {
    'BaseComponent._enabling': True,
    'BaseComponent._disabling': True,
}


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print('Tests complétés du module base_component.')


