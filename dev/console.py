from __future__ import annotations

from ctypes import Structure, wintypes, c_short, c_ulong, c_bool, c_wchar, c_wchar_p, byref, WinDLL, windll
from msvcrt import kbhit, getch
import sys
from enum import Enum, IntEnum

from threading import Thread


# -----------------------------------
# ----------- PRIVATE API -----------
# --- Windows Console API Wrapper ---
# -----------------------------------
class _COORD(Structure):
    _fields_ = [("X", c_short),
                ("Y", c_short)]

class _SMALL_RECT(Structure):
    _fields_ = [("Left", c_short),
                ("Top", c_short),
                ("Right", c_short),
                ("Bottom", c_short)]

class _CONSOLE_SCREEN_BUFFER_INFO(Structure):
    _fields_ = [("dwSize", _COORD),
                ("dwCursorPosition", _COORD),
                ("wAttributes", wintypes.WORD),
                ("srWindow", _SMALL_RECT),
                ("dwMaximumWindowSize", _COORD)]

class _CONSOLE_CURSOR_INFO(Structure):
    _fields_ = [("dwSize", c_ulong),
                ("bVisible", c_bool)]    
# -----------------------------------
# -----------------------------------
# -----------------------------------








class Console:
    """
    Classe pour interagir avec la console Windows, offrant des contrôles
    sur la position du curseur, la visibilité, les couleurs, l'entrée clavier et quelques utilitaires.

    Les sous-types sont :
    - Color : Enumération des couleurs de console pour le texte et le fond.
    - SpecialKey : Enumération pour les touches spéciales du clavier.

    Les propriétés sont :
    - window_size : tuple[int, int]               {read-write} <<< la taille de la fenêtre console
    - cursor_position : tuple[int, int]           {read-write} <<< la position du curseur (colonne, ligne)
    - cursor_visible : bool                       {read-write} <<< visibilité du curseur (True ou False)
    - text_color : Color                          {read-write} <<< couleur du texte (premier plan)
    - background_color : Color                    {read-write} <<< couleur de fond du texte (arrière-plan)
    - key_pressed : list[str | SpecialKey]        {read-only}  <<< détecte la dernière touche frappée et mise en buffer par la console (événementiel)
    - actual_key_pressed : list[str | SpecialKey] {read-only}  <<< liste les touches actuellement maintenues enfoncées sur le clavier (état instantané)

    Les fonctions utilitaires sont :
    - write( text: str
           , position: tuple[int, int] | None = None)
    - clear()
    - reset_colors()
    - restore_initial_state()
   -> wait_for_key_press() -> str | SpecialKey
   -> sleep(duration_millisecond: int)
   -> beep_until(self, frequency: int, duration: int = 250)
    - beep(frequency: int, duration: int = 250)

    > ATTENTION, ces fonctions sont BLOQUANTES et ne sont pas vraiment utiles pour ce projet.

    Supporte le protocole de gestionnaire de contexte (with), qui garantit la
    restauration automatique de l'état initial de la console à la sortie du bloc,
    même en cas d'exception :

        with Console() as console:
            console.text_color = Console.Color.RED
            console.write("Hello!")
        # état initial restauré ici automatiquement

    """

    class Color(Enum):
        """Énumération des couleurs de console pour le texte et le fond."""
        BLACK = 0x0000
        BLUE = 0x0001
        GREEN = 0x0002
        CYAN = 0x0003
        RED = 0x0004
        MAGENTA = 0x0005
        YELLOW = 0x0006 # Souvent affiché comme marron/orange foncé dans les anciennes consoles
        GREY = 0x0007 # Aussi appelé 'WHITE' non intense
        DARK_GREY = 0x0008 # Aussi appelé 'INTENSITY_BLACK' ou 'BLACK' intense
        LIGHT_BLUE = 0x0009
        LIGHT_GREEN = 0x000A
        LIGHT_CYAN = 0x000B
        LIGHT_RED = 0x000C
        LIGHT_MAGENTA = 0x000D
        LIGHT_YELLOW = 0x000E
        WHITE = 0x000F # 'GREY' intense

        @staticmethod
        def _from_win_attrib(attrib_value: int, is_background: bool) -> Console.Color:
            if is_background:
                # Décaler les bits de fond pour correspondre aux valeurs de premier plan
                color_val = (attrib_value & 0x00F0) >> 4
            else:
                color_val = attrib_value & 0x000F
            
            for color in Console.Color:
                if color.value == color_val:
                    return color
            return Console.Color.GREY # Couleur par défaut en cas de non-correspondance

    class SpecialKey(IntEnum):
        """Énumération pour les touches spéciales du clavier."""
        UP_ARROW = 0x48
        DOWN_ARROW = 0x50
        LEFT_ARROW = 0x4B
        RIGHT_ARROW = 0x4D
        DELETE = 0x53
        INSERT = 0x52
        HOME = 0x47
        END = 0x4F
        PAGE_UP = 0x49
        PAGE_DOWN = 0x51
        F1 = 0x3B
        F2 = 0x3C
        F3 = 0x3D
        F4 = 0x3E
        F5 = 0x3F
        F6 = 0x40
        F7 = 0x41
        F8 = 0x42
        F9 = 0x43
        F10 = 0x44
        F11 = 0x85 # Peut varier, basé sur les codes étendus communs
        F12 = 0x86 # Peut varier
        ESC = 0x01 # Mappage interne pour la touche Échap (code réel de msvcrt.getch() est b'\x1b')
        ENTER = 0x0D # Mappage interne pour la touche Entrée (code réel de msvcrt.getch() est b'\r')
        TAB = 0x09 # Mappage interne pour la touche Tab (code réel de msvcrt.getch() est b'\t')
        BACKSPACE = 0x08 # Mappage interne pour la touche Retour arrière (code réel de msvcrt.getch() est b'\x08')
        SHIFT = 256
        CONTROL = 257
        ALT = 258 # VK_MENU
        SPACE = 259        
        # ... autres touches spéciales peuvent être ajoutées
        UNKNOWN = -1


    _STD_OUTPUT_HANDLE_ID: int = -11
    _STD_INPUT_HANDLE_ID: int = -10
    _DEFAULT_CURSOR_SIZE: int = 25 # Pourcentage

    _user32: WinDLL = windll.user32
    _kernel32: WinDLL = windll.kernel32
    _VK_MAP: dict[int, str | SpecialKey] = {} # Doit être initialisé une fois
    _vk_map_initialized: bool = False

    @staticmethod
    def _initialize_vk_map():
        if Console._vk_map_initialized:
            return

        # Définition des codes de touches virtuelles (VK codes)
        # et mappage vers str ou Console.SpecialKey
        # Source: https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
        Console._VK_MAP.update({
            0x08: Console.SpecialKey.BACKSPACE,  # VK_BACK
            0x09: Console.SpecialKey.TAB,        # VK_TAB
            0x0D: Console.SpecialKey.ENTER,      # VK_RETURN
            0x10: Console.SpecialKey.SHIFT,      # VK_SHIFT
            0x11: Console.SpecialKey.CONTROL,    # VK_CONTROL
            0x12: Console.SpecialKey.ALT,        # VK_MENU (Alt)
            0x1B: Console.SpecialKey.ESC,        # VK_ESCAPE
            0x20: Console.SpecialKey.SPACE,      # VK_SPACE
            0x25: Console.SpecialKey.LEFT_ARROW, # VK_LEFT
            0x26: Console.SpecialKey.UP_ARROW,   # VK_UP
            0x27: Console.SpecialKey.RIGHT_ARROW,# VK_RIGHT
            0x28: Console.SpecialKey.DOWN_ARROW, # VK_DOWN
            0x2D: Console.SpecialKey.INSERT,     # VK_INSERT
            0x2E: Console.SpecialKey.DELETE,     # VK_DELETE
            0x24: Console.SpecialKey.HOME,       # VK_HOME
            0x23: Console.SpecialKey.END,        # VK_END
            0x21: Console.SpecialKey.PAGE_UP,    # VK_PRIOR (Page Up)
            0x22: Console.SpecialKey.PAGE_DOWN,  # VK_NEXT (Page Down)
        })

        # Touches de fonction F1-F12 (VK_F1 à VK_F12: 0x70 à 0x7B)
        f_keys_special = [
            Console.SpecialKey.F1, Console.SpecialKey.F2, Console.SpecialKey.F3,
            Console.SpecialKey.F4, Console.SpecialKey.F5, Console.SpecialKey.F6,
            Console.SpecialKey.F7, Console.SpecialKey.F8, Console.SpecialKey.F9,
            Console.SpecialKey.F10, Console.SpecialKey.F11, Console.SpecialKey.F12,
        ]
        for i in range(12):
            Console._VK_MAP[0x70 + i] = f_keys_special[i]

        # Lettres A-Z (VK codes 0x41 à 0x5A)
        for i in range(0x41, 0x5A + 1):
            Console._VK_MAP[i] = chr(i).lower() # Retourne la lettre minuscule

        # Chiffres 0-9 (au-dessus des lettres) (VK codes 0x30 à 0x39)
        for i in range(0x30, 0x39 + 1):
            Console._VK_MAP[i] = chr(i)

        # Chiffres du pavé numérique (VK_NUMPAD0 à VK_NUMPAD9: 0x60 à 0x69)
        # Pour l'instant, mappés aux mêmes chiffres que ceux du haut.
        # On pourrait créer des SpecialKey.NUMPAD0, etc. si une distinction est nécessaire.
        for i in range(10):
            Console._VK_MAP[0x60 + i] = str(i)
            
        # Autres touches du pavé numérique (optionnel, à étendre si besoin)
        # VK_MULTIPLY  0x6A ('*')
        # VK_ADD       0x6B ('+')
        # VK_SEPARATOR 0x6C (varie)
        # VK_SUBTRACT  0x6D ('-')
        # VK_DECIMAL   0x6E ('.')
        # VK_DIVIDE    0x6F ('/')

        Console._vk_map_initialized = True    

    def __enter__(self) -> Console:
        return self

    def __exit__(self, _exc_type: object, _exc_val: object, _exc_tb: object) -> None:
        self.restore_initial_state()

    def __init__(self) -> None:
        self._handle_out = windll.kernel32.GetStdHandle(self._STD_OUTPUT_HANDLE_ID)
        self._handle_in = windll.kernel32.GetStdHandle(self._STD_INPUT_HANDLE_ID)

        # S'assurer que le mappage est prêt
        Console._initialize_vk_map()

        self._beep_thread_started: bool = False

        # Sauvegarder l'état initial de la console
        self._initial_screen_info = self._get_screen_buffer_info()
        self._initial_cursor_info = self._get_cursor_info()
        if self._initial_cursor_info:
            self._initial_cursor_visible = self._initial_cursor_info.bVisible
            self._initial_cursor_size = self._initial_cursor_info.dwSize
        else: # Fallback
            self._initial_cursor_visible = True
            self._initial_cursor_size = self._DEFAULT_CURSOR_SIZE

        if self._initial_screen_info:
            self._initial_attributes = self._initial_screen_info.wAttributes
        else: # Fallback (gris sur noir)
             self._initial_attributes = Console.Color.GREY.value | (Console.Color.BLACK.value << 4)


    def _get_screen_buffer_info(self) -> _CONSOLE_SCREEN_BUFFER_INFO | None:
        csbi = _CONSOLE_SCREEN_BUFFER_INFO()
        if windll.kernel32.GetConsoleScreenBufferInfo(self._handle_out, byref(csbi)):
            return csbi
        return None

    def _get_cursor_info(self) -> _CONSOLE_CURSOR_INFO | None:
        ci = _CONSOLE_CURSOR_INFO()
        if windll.kernel32.GetConsoleCursorInfo(self._handle_out, byref(ci)):
            return ci
        return None
    
    def _set_window_size(self, cols: int, rows: int) -> bool:
        csbi = self._get_screen_buffer_info()
        if not csbi:
            return False
        new_buf = _COORD(max(cols, csbi.dwSize.X), max(rows, csbi.dwSize.Y))
        if not windll.kernel32.SetConsoleScreenBufferSize(self._handle_out, new_buf):
            return False
        win_rect = _SMALL_RECT(0, 0, cols - 1, rows - 1)
        if not windll.kernel32.SetConsoleWindowInfo(self._handle_out, True, byref(win_rect)):
            return False
        self.cursor_position = (
            min(self.cursor_position[0], cols - 1),
            min(self.cursor_position[1], rows - 1)
        )
        return True    

    @property
    def window_size(self) -> tuple[int, int]:
        csbi = self._get_screen_buffer_info()
        if not csbi:
            return (0, 0)
        width  = csbi.srWindow.Right  - csbi.srWindow.Left  + 1
        height = csbi.srWindow.Bottom - csbi.srWindow.Top   + 1
        return (width, height)

    @window_size.setter
    def window_size(self, size: tuple[int, int]) -> None:
        if not self._set_window_size(*size):
            # ici on choisit : lever ou silencieux
            raise RuntimeError("Impossible de redimensionner la fenêtre.")
    
    @property
    def cursor_position(self) -> tuple[int, int]:
        """
        Obtient ou définit la position actuelle du curseur (colonne, ligne).
        Les coordonnées sont basées sur 0.
        """
        csbi = self._get_screen_buffer_info()
        if csbi:
            return (csbi.dwCursorPosition.X, csbi.dwCursorPosition.Y)
        return (0, 0) # Fallback

    @cursor_position.setter
    def cursor_position(self, position: tuple[int, int]) -> None:
        x, y = position
        if not (isinstance(x, int) and isinstance(y, int) and x >= 0 and y >= 0): # type: ignore[reportUnnecessaryIsInstance]
            raise ValueError("La position du curseur doit être un tuple d'entiers positifs (x, y).")
        new_pos = _COORD(x, y)
        windll.kernel32.SetConsoleCursorPosition(self._handle_out, new_pos)

    @property
    def cursor_visible(self) -> bool:
        """
        Obtient ou définit la visibilité du curseur.
        True pour visible, False pour invisible.
        """
        ci = self._get_cursor_info()
        if ci:
            return ci.bVisible
        return True # Fallback

    @cursor_visible.setter
    def cursor_visible(self, visible: bool) -> None:
        if not isinstance(visible, bool): # type: ignore[reportUnnecessaryIsInstance]
            raise TypeError("La visibilité du curseur doit être un booléen.")
        ci = self._get_cursor_info()
        if not ci: # Ne peut pas obtenir l'info actuelle, ne peut pas la définir de manière fiable.
            return

        current_size = ci.dwSize
        if visible and (current_size < 1 or current_size > 100) : # si visible et taille invalide (ex: après avoir été caché)
            current_size = self._DEFAULT_CURSOR_SIZE

        new_ci = _CONSOLE_CURSOR_INFO(current_size, visible)
        windll.kernel32.SetConsoleCursorInfo(self._handle_out, byref(new_ci))

    @property
    def text_color(self) -> Color:
        """
        Obtient ou définit la couleur du texte (premier plan).
        Utilise l'énumération ConsoleColor.
        """
        csbi = self._get_screen_buffer_info()
        if csbi:
            return Console.Color._from_win_attrib(csbi.wAttributes, is_background=False) # pyright: ignore[reportPrivateUsage] | FRIEND ACCESS
        return Console.Color.GREY # Fallback

    @text_color.setter
    def text_color(self, color: Color) -> None:
        if not isinstance(color, Console.Color): # type: ignore[reportUnnecessaryIsInstance]
            raise TypeError("La couleur du texte doit être un membre de l'énumération ConsoleColor.")
        csbi = self._get_screen_buffer_info()
        current_attributes = csbi.wAttributes if csbi else self._initial_attributes
        
        # Préserver la couleur de fond actuelle
        background_mask = 0x00F0
        current_background = current_attributes & background_mask
        
        new_attributes = color.value | current_background
        windll.kernel32.SetConsoleTextAttribute(self._handle_out, new_attributes)

    @property
    def background_color(self) -> Color:
        """
        Obtient ou définit la couleur de fond du texte.
        Utilise l'énumération ConsoleColor.
        """
        csbi = self._get_screen_buffer_info()
        if csbi:
            return Console.Color._from_win_attrib(csbi.wAttributes, is_background=True) # pyright: ignore[reportPrivateUsage] | FRIEND ACCESS
        return Console.Color.BLACK # Fallback

    @background_color.setter
    def background_color(self, color: Color) -> None:
        if not isinstance(color, Console.Color): # type: ignore[reportUnnecessaryIsInstance]
            raise TypeError("La couleur de fond doit être un membre de l'énumération ConsoleColor.")
        csbi = self._get_screen_buffer_info()
        current_attributes = csbi.wAttributes if csbi else self._initial_attributes

        # Préserver la couleur de premier plan actuelle
        foreground_mask = 0x000F
        current_foreground = current_attributes & foreground_mask
        
        # Les valeurs de ConsoleColor sont pour le premier plan.
        # Pour le fond, elles doivent être décalées de 4 bits vers la gauche.
        new_background_val = color.value << 4
        new_attributes = current_foreground | new_background_val
        windll.kernel32.SetConsoleTextAttribute(self._handle_out, new_attributes)

    @property
    def key_pressed(self) -> list[str | SpecialKey]:
        """
        Vérifie si une touche est appuyée et retourne la ou les touches.
        Retourne une liste vide si aucune touche n'est appuyée.
        Les caractères normaux sont retournés comme chaînes, les touches 
        spéciales comme membres de l'énumération SpecialKey.

        Retourne la ou les touches d'un événement de frappe récent, lues depuis 
        le buffer d'entrée de la console via msvcrt.getch(). Elle retourne 
        aussi des touches qui ont été appuyées dans le passée. Non bloquante 
        (grâce à msvcrt.kbhit()), elle capture une action de touche unique qui 
        s'est produite. Idéale pour une saisie séquentielle ou des commandes 
        déclenchées par une frappe.
        """
        keys_pressed: list[str | Console.SpecialKey] = []
        if kbhit():
            char_bytes = getch()
            
            # Gérer les caractères simples et certaines touches de contrôle directes
            if char_bytes == b'\r': # Entrée
                keys_pressed.append(Console.SpecialKey.ENTER)
                return keys_pressed
            elif char_bytes == b'\x1b': # Échap
                keys_pressed.append(Console.SpecialKey.ESC)
                return keys_pressed
            elif char_bytes == b'\t': # Tab
                keys_pressed.append(Console.SpecialKey.TAB)
                return keys_pressed
            elif char_bytes == b'\x08': # Retour arrière
                keys_pressed.append(Console.SpecialKey.BACKSPACE)
                return keys_pressed
            elif char_bytes == b' ': # Espace
                keys_pressed.append(Console.SpecialKey.SPACE)
                return keys_pressed

            # Gérer les touches spéciales (préfixées)
            if char_bytes == b'\x00' or char_bytes == b'\xe0':
                second_byte = getch()
                code_val = second_byte[0] # Obtenir la valeur entière du byte
                found_special_key = False
                for skey in Console.SpecialKey:
                    if skey.value == code_val:
                        keys_pressed.append(skey)
                        found_special_key = True
                        break
                if not found_special_key:
                    keys_pressed.append(Console.SpecialKey.UNKNOWN) # Ou gérer autrement
            else: # Caractère normal
                try:
                    keys_pressed.append(char_bytes.decode('utf-8', errors='replace'))
                except UnicodeDecodeError: # Fallback si le décodage échoue
                    # Tenter avec l'encodage de la console, sinon brut
                    try:
                        console_encoding = sys.stdout.encoding or 'cp1252' # ou get_console_cp()
                        keys_pressed.append(char_bytes.decode(console_encoding, errors='replace'))
                    except Exception:
                         keys_pressed.append(f"RAW_BYTE_0x{char_bytes.hex()}")

        return keys_pressed
    
    @property
    def actual_key_pressed(self) -> list[str | SpecialKey]:
        """
        Vérifie l'état actuel de toutes les touches mappées et retourne celles
        qui sont actuellement enfoncées.
        Retourne une liste de chaînes (pour les caractères) ou de SpecialKey.
        Cette méthode utilise GetAsyncKeyState et reflète l'état physique des 
        touches.

        Fournit un instantané de toutes les touches physiquement maintenues 
        enfoncées au moment de l'appel, en interrogeant l'état du clavier via 
        GetAsyncKeyState. Permet de vérifier l'état simultané de plusieurs 
        touches, utile pour des contrôles continus (ex: mouvement) ou la 
        détection de combinaisons.
        """
        pressed_keys_set: set[str | Console.SpecialKey] = set()

        for vk_code, key_representation in Console._VK_MAP.items():
            # Le bit de poids fort (0x8000) est à 1 si la touche est enfoncée.
            if self._user32.GetAsyncKeyState(vk_code) & 0x8000:
                pressed_keys_set.add(key_representation)
        
        return list(pressed_keys_set)

    def write(self, text: str, position: tuple[int, int] | None = None) -> None:
        """
        Écrit du texte à la position actuelle ou spécifiée du curseur.

        Args:
            text (str): Le texte à écrire.
            position (tuple[int, int] | None): Si fourni, définit la position
                                               du curseur avant d'écrire.
                                               Si None, écrit à la position 
                                               actuelle du curseur.
        """
        if position is not None:
            self.cursor_position = position
        
        c_text = c_wchar_p(text)
        chars_written = c_ulong(0)
        windll.kernel32.WriteConsoleW(
            self._handle_out,
            c_text,
            len(text),
            byref(chars_written),
            None
        )
        sys.stdout.flush() # Peut être nécessaire dans certains contextes

    def clear(self) -> None:
        """Efface l'écran de la console et replace le curseur en (0,0)
           en utilisant les couleurs actuellement définies.""" # Docstring mise à jour
        csbi = self._get_screen_buffer_info()
        if not csbi:
            # Fallback si on ne peut pas obtenir les infos (moins précis).
            # Note : Ce fallback ne pourra pas utiliser correctement la couleur de fond actuelle
            # car la méthode write() elle-même dépend des attributs courants mais l'effacement
            # par écriture de nouvelles lignes est une approximation.
            self.cursor_position = (0,0)
            # Sauvegarder les couleurs actuelles pour le fallback
            current_fg = self.text_color
            current_bg = self.background_color
            self.write("\n" * (self.window_size[1] if self.window_size[1] > 0 else 50) ) # write utilise les attributs courants
            # Restaurer les couleurs au cas où write les aurait modifiées (peu probable ici)
            self.text_color = current_fg
            self.background_color = current_bg
            self.cursor_position = (0,0)
            return

        console_size = csbi.dwSize.X * csbi.dwSize.Y
        coord_screen = _COORD(0, 0)
        chars_written = c_ulong(0)

        # Remplir le buffer avec des espaces
        windll.kernel32.FillConsoleOutputCharacterW(
            self._handle_out,
            c_wchar(' '),
            console_size,
            coord_screen,
            byref(chars_written)
        )

        # Récupérer les attributs actuels de la console (qui incluent la couleur de fond et de texte définie)
        # csbi.wAttributes reflète les derniers attributs définis par SetConsoleTextAttribute.
        attributes_to_fill_with = csbi.wAttributes

        # Remplir les attributs du buffer avec les attributs ACTUELS
        windll.kernel32.FillConsoleOutputAttribute(
            self._handle_out,
            attributes_to_fill_with, # Utiliser les attributs actuels
            console_size,
            coord_screen,
            byref(chars_written)
        )
        self.cursor_position = (0, 0)
        
    def reset_colors(self) -> None:
        """Réinitialise les couleurs du texte et du fond à des valeurs par défaut (gris sur noir)."""
        self.text_color = Console.Color.GREY
        self.background_color = Console.Color.BLACK
    
    def restore_initial_state(self) -> None:
        """Restaure la console à son état (couleurs, visibilité/taille du curseur)
           lors de l'instanciation de l'objet WindowsConsole."""
        windll.kernel32.SetConsoleTextAttribute(self._handle_out, self._initial_attributes)
        
        initial_cursor_info = _CONSOLE_CURSOR_INFO(self._initial_cursor_size, self._initial_cursor_visible)
        windll.kernel32.SetConsoleCursorInfo(self._handle_out, byref(initial_cursor_info))
        
        if self._initial_screen_info:
            self.cursor_position = (self._initial_screen_info.dwCursorPosition.X, self._initial_screen_info.dwCursorPosition.Y)

    def sleep(self, duration_millisecond: int) -> None:
        """Met le thread en pause pour une durée spécifiée (en millisecondes).
        
        ATTENTION, cette fonction est BLOQUANTE. Elle n'est pas vraiment utile 
        pour ce projet mais peut servir pour des tests en phase préliminaire.

        Args:
            duration_millisecond (int): Durée de la pause en millisecondes.
        
        Raises:
            ValueError: Si la durée est négative ou non entière.
        """
        if duration_millisecond < 0:
            raise ValueError("La durée doit être un entier positif.")
        windll.kernel32.Sleep(duration_millisecond)

    def wait_for_key_press(self) -> str | Console.SpecialKey:
        """Bloque jusqu'à ce qu'une touche soit pressée et la retourne.

        Les touches déjà présentes dans le buffer de la console sont consommées
        en priorité. Retourne la première touche disponible.

        Returns:
            str | Console.SpecialKey: La touche pressée, sous forme de chaîne
                pour les caractères normaux ou de SpecialKey pour les touches
                spéciales.
        """
        while True:
            keys = self.key_pressed
            if keys:
                return keys[0]
            self.sleep(10)

    def beep_until(self, frequency: int, duration: int = 250) -> None:
        """
        Émet un son (beep) à la fréquence et pour la durée spécifiées.

        ATTENTION, cette fonction est ***BLOQUANTE***. Elle n'est pas vraiment utile 
        pour ce projet mais peut servir pour des tests en phase préliminaire. 
        Voir la fonction suivante pour une version non-bloquante.

        ATTENTION, la fonction beep de Windows ne fonctionne pas sur les systèmes
        Windows Server Core ou les systèmes sans haut-parleur interne. De plus, cette 
        fonction de bas niveau est très peu performante et ne permet pas de faire 
        des effets intéressants et réactifs. Elle ne sert qu'à faire un bip
        simple, pas à jouer de la musique ou des sons complexes. C'est une fonction lente
        pour démarrer et terminer. De plus, elle engage parfois un certain son d'amorçage et 
        de désamorçage du haut-parleur, ce qui peut être gênant. 

        Args:
            frequency (int): La fréquence du son, en hertz (Hz).
                             Doit être comprise entre 37 et 32767.
            duration (int): La durée du son, en millisecondes (ms).
                            Doit être une valeur positive.
        
        Raises:
            ValueError: Si la fréquence ou la durée sont en dehors des plages valides.
            OSError: Si l'appel système à Beep échoue pour une raison quelconque.
        """
        if not (37 <= frequency <= 32767):
            raise ValueError("La fréquence doit être comprise entre 37 et 32767 Hz.")
        if not duration > 0:
            raise ValueError("La durée doit être un entier positif en millisecondes.")

        # self._kernel32 est déjà défini dans votre classe __init__ comme ctypes.windll.kernel32
        if not self._kernel32.Beep(int(frequency), int(duration)):
            # Beep retourne 0 en cas d'échec.
            # Vous pourriez vouloir lever une exception plus spécifique ou gérer l'erreur autrement.
            error_code = self._kernel32.GetLastError()
            raise OSError(f"L'appel à la fonction Beep a échoué avec le code d'erreur Windows : {error_code}")        
        
    def beep(self, frequency: int, duration: int = 250) -> None:
        """
        Émet un son (beep) de manière non bloquante en l'exécutant dans un thread séparé.
        La fonction retourne immédiatement pendant que le son joue en arrière-plan.

        ATTENTION, cette fonction est NON BLOQUANTE.

        ATTENTION, la fonction beep de Windows ne fonctionne pas sur les systèmes
        Windows Server Core ou les systèmes sans haut-parleur interne. De plus, cette 
        fonction de bas niveau est très peu performante et ne permet pas de faire 
        des effets intéressants et réactifs. Elle ne sert qu'à faire un bip
        simple, pas à jouer de la musique ou des sons complexes. C'est une fonction lente
        pour démarrer et terminer. De plus, elle engage parfois un certain son d'amorce et 
        de désamorçage du haut-parleur, ce qui peut être gênant. 
        
        Finalement, le fait qu'elle soit ici dans un thread séparé augmente le niveau de 
        non perforance de la fonction

        Args:
            frequency (int): La fréquence du son, en hertz (Hz).
                             Doit être comprise entre 37 et 32767.
            duration (int): La durée du son, en millisecondes (ms).
                            Doit être une valeur positive.
        
        Note: Les exceptions levées par la validation des arguments (ValueError)
              se produiront immédiatement. Les erreurs d'exécution de Beep (OSError)
              se produiront dans le thread séparé et peuvent être plus difficiles à capturer
              directement par l'appelant.
        """
        if self._beep_thread_started:
            return

        # Valider les arguments immédiatement dans le thread principal
        if not (37 <= frequency <= 32767):
            raise ValueError("La fréquence doit être comprise entre 37 et 32767 Hz.")
        if not duration > 0:
            raise ValueError("La durée doit être un entier positif en millisecondes.")

        def _beep_task():
            try:
                if not self._kernel32.Beep(int(frequency), int(duration)):
                    # Beep retourne 0 en cas d'échec.
                    # Vous pourriez vouloir lever une exception plus spécifique ou gérer l'erreur autrement.
                    error_code = self._kernel32.GetLastError()
                    raise OSError(f"L'appel à la fonction Beep a échoué avec le code d'erreur Windows : {error_code}")
            except OSError as e:
                # Optionnel : gérer les erreurs d'exécution de Beep dans le thread
                # Par exemple, les imprimer sur la sortie d'erreur standard.
                # Dans une application plus complexe, vous pourriez utiliser un mécanisme
                # de file d'attente ou de rappel pour signaler les erreurs au thread principal.
                print(f"Erreur système pendant le beep non bloquant: {e}", file=sys.stderr)
            except Exception as e_thread:
                 print(f"Erreur inattendue dans le thread du beep: {e_thread}", file=sys.stderr)
            finally:
                # Assurez-vous que le thread est marqué comme terminé
                self._beep_thread_started = False

        # Créer un nouveau thread qui exécutera la fonction _beep_task
        beep_thread = Thread(target=_beep_task)
        
        # Configurer le thread comme "daemon". Cela signifie que si votre programme principal
        # se termine, ce thread de beep sera automatiquement arrêté. Si daemon=False (par défaut),
        # le programme principal attendrait que le beep finisse (même s'il dure longtemps)
        # avant de pouvoir se fermer complètement. Pour un beep, daemon=True est souvent souhaitable.
        beep_thread.daemon = True
        
        # Démarrer l'exécution du thread
        self._beep_thread_started = True
        beep_thread.start()





# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# DEMOS VARIÉES
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------



def demo_01(console: Console) -> None:
    """Grille des 16 couleurs — démo de couleurs et positionnement.

    Affiche une matrice 4×4 où chaque cellule montre :
      - le nom de la couleur écrit dans cette couleur (texte sur fond noir)
      - une bande de fond dans cette couleur
    """
    CELL_W  = 18   # largeur d'une cellule
    CELL_H  = 3    # hauteur d'une cellule (nom + bande + séparateur)
    COLS    = 4
    ORIGIN_X, ORIGIN_Y = 2, 2

    console.clear()
    console.background_color = Console.Color.BLACK
    console.text_color = Console.Color.WHITE
    console.write("Palette des 16 couleurs — texte et fond", (ORIGIN_X, 0))
    console.write(f"{'NOM':<{CELL_W}}{'NOM':<{CELL_W}}{'NOM':<{CELL_W}}{'NOM':<{CELL_W}}", (ORIGIN_X, 1))

    colors = list(Console.Color)
    for i, color in enumerate(colors):
        col = i % COLS
        row = i // COLS
        cx = ORIGIN_X + col * CELL_W
        cy = ORIGIN_Y + row * CELL_H

        # Ligne 1 : nom de la couleur écrit dans sa propre couleur
        name_color = Console.Color.GREY if color == Console.Color.BLACK else color
        console.background_color = Console.Color.BLACK
        console.text_color = name_color
        console.write(f"{color.name:<{CELL_W}}", (cx, cy))

        # Ligne 2 : bande de fond dans la couleur (espaces = fond visible)
        console.background_color = color
        console.write(" " * CELL_W, (cx, cy + 1))

    console.reset_colors()
    console.cursor_position = (ORIGIN_X, ORIGIN_Y + COLS * CELL_H)
    console.write("Appuyez sur une touche pour continuer...", (ORIGIN_X, ORIGIN_Y + COLS * CELL_H + 1))
    console.wait_for_key_press()
    console.restore_initial_state()

def demo_02(console: Console) -> None:
    """Visibilité du curseur
    
    Démontre cursor_visible en masquant le curseur pendant un rendu
    (évite le scintillement lors d'écritures multiples), puis le
    restaure.
    NOTE : SetConsoleCursorInfo (API Win32) est ignoré par le terminal
    intégré de VSCode — cette section fonctionne dans cmd.exe natif.
    """
    console.clear()
    console.write("Démonstration de la visibilité du curseur", (0, 0))

    original_visibility = console.cursor_visible

    console.text_color = Console.Color.DARK_GREY
    console.write("(!) Résultat visible en cmd.exe — voir commentaires §3", (0, 2))

    # Masquer le curseur pour simuler un rendu sans scintillement
    console.cursor_visible = False
    console.text_color = Console.Color.WHITE
    console.write("Curseur masqué  — rendu en cours...", (0, 3))
    for col in range(40):
        console.text_color = Console.Color.LIGHT_GREEN if col % 2 == 0 else Console.Color.LIGHT_YELLOW
        console.cursor_position = (col, 4)
        console.write("*")
        console.sleep(40)

    # Restaurer la visibilité initiale
    console.cursor_visible = original_visibility
    console.text_color = Console.Color.WHITE
    console.write("Curseur restauré — rendu terminé.  ", (0, 3))
    console.write("Appuyez sur une touche pour continuer...", (0, 5))
    console.wait_for_key_press()

def demo_03(console: Console) -> None:
    """Saisie de texte avec key_pressed (événementiel)

    - Chaque frappe est capturée dans l'ordre depuis le buffer.
    - Aucune frappe n'est perdue, même si l'utilisateur tape vite.
    - BACKSPACE efface le dernier caractère saisi.
    - ENTER confirme la saisie ; ÉCHAP passe à la section suivante.
    """
    INPUT_Y   = 2
    RESULT_Y  = 4
    MAX_LEN   = 40
    console.clear()
    console.write("Saisie de texte avec key_pressed (événementiel)", (0, 0))

    console.text_color    = Console.Color.CYAN
    console.background_color = Console.Color.BLACK
    console.cursor_visible = False
    console.write("Saisie de texte (ENTER pour confirmer, ÉCHAP pour passer) :", (0, INPUT_Y - 1))

    typed: list[str] = []
    confirmed_lines: list[str] = []

    while True:
        # Afficher le texte en cours de saisie
        display = "".join(typed)
        console.text_color = Console.Color.WHITE
        console.cursor_position = (0, INPUT_Y)
        console.write(f"> {display:<{MAX_LEN}}")
        console.cursor_position = (2 + len(typed), INPUT_Y)

        keys = console.key_pressed
        if not keys:
            continue

        key = keys[0]

        if isinstance(key, Console.SpecialKey):
            if key == Console.SpecialKey.ESC:
                break
            elif key == Console.SpecialKey.ENTER and typed:
                confirmed_lines.append("".join(typed))
                typed = []
                # Afficher les lignes confirmées
                console.text_color = Console.Color.LIGHT_GREEN
                for i, line in enumerate(confirmed_lines[-3:]):  # 3 dernières max
                    console.cursor_position = (0, RESULT_Y + i)
                    console.write(f"  \"{line}\"" + " " * (MAX_LEN - len(line)))
            elif key == Console.SpecialKey.BACKSPACE and typed:
                typed.pop()
        elif not isinstance(key, Console.SpecialKey) and len(typed) < MAX_LEN:
            typed.append(key)


def demo_04(console: Console) -> None:
    """Lecture instantanée des touches (actual_key_pressed)
    
    - Reflète l'état physique du clavier au moment de l'appel.
    - Détecte les touches maintenues enfoncées simultanément.
    - Déplacer '@' avec les flèches ; SHIFT pour accélérer (pas=3).
    - Déplacement diagonal possible (deux flèches simultanées).
    - Appuyez sur DELETE pour terminer l'exemple.
    """
    ARENA_X, ARENA_Y  = 0, 0
    ARENA_W, ARENA_H  = 60, 10

    # Dessiner le cadre de l'arène
    console.clear()
    console.text_color   = Console.Color.GREY
    console.cursor_position = (ARENA_X, ARENA_Y)
    console.write("Flèches = déplacer '@'  |  SHIFT = accélérer  |  DELETE = quitter")
    console.cursor_position = (ARENA_X, ARENA_Y + 1)
    console.write("+" + "-" * ARENA_W + "+")
    for row in range(ARENA_H):
        console.cursor_position = (ARENA_X, ARENA_Y + 2 + row)
        console.write("|" + " " * ARENA_W + "|")
    console.cursor_position = (ARENA_X, ARENA_Y + 2 + ARENA_H)
    console.write("+" + "-" * ARENA_W + "+")

    px, py = ARENA_W // 2, ARENA_H // 2   # position initiale du marqueur

    while True:
        pressed_keys = console.actual_key_pressed

        if Console.SpecialKey.DELETE in pressed_keys:
            break

        step = 3 if Console.SpecialKey.SHIFT in pressed_keys else 1

        dx = dy = 0
        if Console.SpecialKey.LEFT_ARROW  in pressed_keys: dx -= step
        if Console.SpecialKey.RIGHT_ARROW in pressed_keys: dx += step
        if Console.SpecialKey.UP_ARROW    in pressed_keys: dy -= step
        if Console.SpecialKey.DOWN_ARROW  in pressed_keys: dy += step

        if dx != 0 or dy != 0:
            # Effacer l'ancienne position
            console.text_color = Console.Color.BLACK
            console.cursor_position = (ARENA_X + 1 + px, ARENA_Y + 2 + py)
            console.write(" ")

            # Déplacer en restant dans l'arène
            px = max(0, min(ARENA_W - 1, px + dx))
            py = max(0, min(ARENA_H - 1, py + dy))

            # Dessiner à la nouvelle position
            console.text_color = Console.Color.LIGHT_YELLOW
            console.cursor_position = (ARENA_X + 1 + px, ARENA_Y + 2 + py)
            console.write("@")

        console.sleep(30)    

    console.clear()


def main() -> None:
    try:
        # Le gestionnaire de contexte garantit la restauration de l'état initial,
        # même en cas d'exception non gérée.
        with Console() as console:

            # Initialisation de la fenêtre
            console.beep_until(440)
            console.window_size = (100, 30)
            console.background_color = Console.Color.BLACK
            console.clear()

            # Demo les unes après les autres
            demo_01(console)
            demo_02(console)
            demo_03(console)
            demo_04(console)

        # # Restauration automatique effectuée par le context manager (__exit__)
        print("\nExemple terminé. L'état initial de la console a été restauré.")

    except Exception as e:
        print(f"\nUne erreur est survenue: {e}")

if __name__ == '__main__':
    main()

