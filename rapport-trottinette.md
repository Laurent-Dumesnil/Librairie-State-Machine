# Rapport

## Équipe

Lamontagne, Julien :869558  
Boumazouzi, Yanis :2290619  
Dumesnil, Laurent : 1379670  
Proulx, Jérémie : 1746047  
Isabelle Ndioukane, Marie Joëlle : 2363434
Forest Martinez, Isabela : 2177448  

## États ayant une machine d’états
On transforme les états `Charging`et `Scooting` en sous-classes de `MonitoredState` afin d'en hériter ses propriétés. On leur assigne, à chacune d'entre-elles, une machine d'états via une classe imbriquée héritée de `StateMachineDevice` (soit `BatteryManagement` et `RideManagement`). De cette façon, elles seront capables de disposer d'états, de transitions, de conditions et d'un layout. Dans le constructeur des états `Charging` et `Scooting`, on instancie la classe imbriquée en tant que variable privée. Par la suite, on redéfinit trois méthodes de `MonitoredState` :
 
-  ` _do_in_state_action` suit l'état du dispositif en appelant la méthode `track` comme action pendant pendant l'exécution de l'état.
- ` _do_entering_action` active la machine d'états interne comme action d'entrée de l'état.
- ` _do_exiting_action` désactive la machine d'états interne comme action de sortie de l'état.

Cette nouvelle abstraction apporte une séparation des responsabilités au sein de la machine d'états principale. Plutôt que de surcharger celle-ci avec tous les états liés au mouvement et à la recharge, on délègue ces comportements à des machines d'états internes encapsulées dans leurs états respectifs. Cela rend la machine d'états principale plus lisible et chaque sous-machine réutilisable.

Pour rendre le concept générique, nous pouvons introduire une nouvelle abstraction `InnerStateMachine` héritant de `MonitoredState`. Celle-ci gèrerait automatiquement l'activation, la désactivation et le suivi de la machine d'états interne, ce qui permettra de ne plus avoir besoin de redéfinir les méthodes d'état à chaque définition de classe.
## Compréhension générale
Le diagramme d'état de transition du scooter présente deux limitations techniques : 
- Dans l'état `powering_down`, la valeur `custom_value` n'est jamais assignée par les transitions. Aucunes d'entre elles proviennent de l'énumérateur `PoweringDownMode` alors qu'il est explicitement écrit que le comportement de l'état dépend de ladite valeur.
- L'usage de l'état `unlocking` n'est pas pertinent dans ce contexte. Sa seule utilité est de transiter l'état `power_off` vers `powering_up` après 3 secondes, ce qui aurait pu être réalisé en y ajoutant directement la condition dans la transition. De plus, la vérification d'accès est de toute façon prise en charge par `powering_up` via `integrity_failed`.
## Évaluation des objectifs
Nous avons compléter tous les éléments demandés par le mandat. Par conséquent, aucune liste n'a été produite.
## Ajout personnel 
- L'ajout de l'option d'un Cruise Control permet de maintenir une vitesse constante de la trotinnette sans avoir à l'accélérer. Pour se faire, nous avons implémenté l'état `cruise_control_state` dans la machine d'états `RideManagement` en appuyant sur la touche 'c' depuis l'état `free_wheel_state`.
- L'utilitaire `DelaySinceBelowThresholdCondition` devient `True` si une valeur reste sous un seuil donné pendant une durée déterminée. La logique est définie dans la méthode surchargée `_compare` selon trois cas :
-- La valeur est au-dessus du seuil → `False`
-- La valeur passe sous le seuil pour la première fois → démarre le timer, `False`
-- Le timer dépasse la durée → `True`
- L'utilitaire `LessThanValueCondition` devient `True` si la valeur dynamique examinée `value_reader` est plus petite que `target_value`. Cette condition est vérifiée via la méthode `compare`.
- L'utilitaire `KeyPressCondition` devient `True` si la touche appuyé au clavier correspond à la touche voulu. `compare` vérifie si ladite touche fait partie de `key_reader`.
## Réponses aux 2 questions par chacun des étudiants de l'équipe

1. Considérant les phases 1 à 4 de la bibliothèque, nommez les deux parties que vous avez trouvé le plus intéressant et le plus difficile.
2. Considérant le mandat de la fin alternative, discuter de sa pertinence dans le cadre de réalisation d’un projet valorisant la bibliothèque développées. 

#### Julien

1. 
2.

#### Yanis

1. 
2.

#### Laurent

1. 
2.

#### Jérémie

1. La partie que j'ai trouvé la plus intéressante est la partie 3 du projet, car c'est à cette étape que l'on commence à comprendre ce sur quoi nous travaillons. En ajoutant les transitions et les conditions, l'utilité du projet devient de plus en plus clair et il devient donc plus facile de coder les méthodes demandées. À l'inverse, la partie que j'ai trouvé la plus difficile est la partie 1, car au début, nous nous contentions d'essayer de reproduire les UML un peu à l'aveugle, sans jamais réellement comprendre ce que nous faisons. Nous avons du à plusieurs reprises revenir sur des parties antérieures au fur et à mesure de l'avancement du projet afin de corriger des parties que nous avions mal compris.
2. Le projet de la trotinette est très intéressant, car il utilise beaucoup de parties de la bibliothèque et nos permet d'avoir un usage concret de comment l'utiliser. Nous avons aussi utilisé certaines parties dont nous nous étions jamais servi auparavant. Par exemple, afin de transmettre la raison de l'erreur aux blinkers afin qu'ils puissent s'allumer de la bonne couleur, j'ai utilisé des ActionTransition et des transiting_action pour sauvergarder l'erreur pendant la transition.

#### Marie Joëlle

1. La partie que j'ai trouvé la plus intéressante est la phase 4, car c'est la première fois qu'on voyait vraiment à quoi servait tout ce qu'on avait construit avant. Faire clignoter un dispositif avec autant de contrôle en aussi peu de code, grâce à la machine d'états, c'était satisfaisant à voir fonctionner. La partie la plus difficile pour moi a été la phase 2, parce que comprendre comment le Layout devait être construit dans la classe enfant avant que le parent termine son initialisation était vraiment contre-intuitif au début. J'ai dû relire le diagramme de séquence plusieurs fois avant de comprendre.
2.Le projet de la trottinette est très pertinent parce qu'il nous permet d'exploiter pleinement les parties de la bibliothèque. Par exemple, le fait d'avoir des états qui contiennent eux-mêmes une machine d'états nous a poussés à réfléchir à un niveau d'abstraction qu'on n'avait pas eu à considérer dans les phases précédentes. Contrairement à un projet plus simple, la trottinette a suffisamment de complexité pour justifier l'usage de toutes les couches qu'on a bâties, ce qui donne un bon aperçu de ce que la bibliothèque peut faire dans un vrai contexte applicatif.

#### Isabela
1. Selon moi, la partie 4 du projet était la plus intéressante. C'est dans cette partie que j'ai réellement pu comprendre le fonctionnement de la bibliothèque ainsi que l'utilité d'utiliser un diagramme d'états-transitions. Avant la création de cette machine d'état, le travail que nous faisions était surtout abstrait. C'est en créant la sous-classe de BlinkerDevice que j'ai pu voir concrètement le fonctionnement d'un StateMachineDevice. La partie que j'ai trouvée la plus difficile était la partie 2. Comprendre comment placer le Layout dans le StateMachineDevice a pris beaucoup de réflexion et ce n'était pas quelque chose que j'avais fait auparavant, alors je n'étais pas confiante sur la méthode à employer.
2. Le mandat de fin alternative est pertinent en termes de voir l'étendue des possibilités de la bibliothèque que nous avons créée. Il présente un projet qui, sans notre bibliothèque, a un niveau de complexité dépassant nos capacités dans le temps donné. On utilise des classes de notre bibliothèque qui nous permettent de passer d'un état de la trottinette à un autre sans avoir à se préoccuper de gérer des timers ou de s'assurer de la validité de nos machines d'états. On a pas besoin de se soucier du nombre de fonctionnalités que la trottinette peut avoir parce que les classes sont faites pour faciliter l'implémentation de nouveaux états sans avoir à tout repasser le code. 
