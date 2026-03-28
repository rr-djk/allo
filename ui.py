"""ui.py — Composants tkinter de l'application record.

Contient :
- MicIcon : fenêtre flottante représentant l'icône micro
"""

import tkinter as tk


# Déplacement maximal en pixels en-deçà duquel un press+release est traité
# comme un clic d'enregistrement plutôt que comme un drag de la fenêtre
_DRAG_THRESHOLD = 5

# Couleur de fond de l'icône micro au repos
_MIC_FILL_COLOR = "#444444"
# Couleur du contour de l'icône micro
_MIC_OUTLINE_COLOR = "#222222"
# Marge intérieure du canvas par rapport à l'ovale
_MIC_PADDING = 5


class MicIcon(tk.Tk):
    """Fenêtre flottante 50x50 représentant l'icône micro.

    Fenêtre sans bordure, toujours au premier plan, contenant un canvas
    avec un ovale symbolisant un microphone.
    """

    def __init__(self, on_record_start=None, on_record_stop=None, on_auto_stop=None, on_quit=None):
        """Initialise la fenêtre et dessine l'icône micro.

        @param on_record_start {callable|None} Rappel invoqué au moment où le
               bouton gauche de la souris est pressé (début d'enregistrement).
               Ignoré si None.
        @param on_record_stop  {callable|None} Rappel invoqué au moment où le
               bouton gauche de la souris est relâché (fin d'enregistrement).
               Ignoré si None.
        @param on_auto_stop    {callable|None} Rappel invoqué lorsque
               l'enregistrement est interrompu automatiquement (timer MAX_DURATION).
               Ignoré si None.
        @param on_quit         {callable|None} Rappel invoqué juste avant la
               destruction de la fenêtre (nettoyage des threads/ressources).
               Ignoré si None.
        """
        super().__init__()
        self._on_record_start = on_record_start
        self._on_record_stop = on_record_stop
        self._on_auto_stop = on_auto_stop
        self._on_quit = on_quit
        self._configure_window()
        self._canvas = self._build_canvas()
        self._draw_mic_icon()
        # Initialisés ici pour éviter une AttributeError si <B1-Motion> est
        # déclenché sans <ButtonPress-1> préalable
        self._drag_start_x = 0
        self._drag_start_y = 0
        # Position absolue (écran) au moment du ButtonPress-1 ; sert à mesurer
        # le déplacement total pour distinguer un clic d'un drag
        self._press_x = 0
        self._press_y = 0
        self._bind_drag()
        self._bind_context_menu()

    def _configure_window(self):
        """Configure les attributs de la fenêtre principale.

        Applique la taille fixe, supprime la bordure système et
        positionne la fenêtre toujours au premier plan.
        """
        self.geometry("50x50")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)

    def _build_canvas(self):
        """Crée et positionne le canvas 50x50 dans la fenêtre.

        @returns {tk.Canvas} Le canvas attaché à la fenêtre.
        """
        canvas = tk.Canvas(
            self,
            width=50,
            height=50,
            highlightthickness=0,
            bg="#333333",
        )
        canvas.pack()
        return canvas

    def _bind_drag(self):
        """Attache les événements souris permettant le déplacement de la fenêtre.

        Lie également <ButtonPress-1> et <ButtonRelease-1> aux rappels
        d'enregistrement fournis à l'initialisation, s'ils sont définis.
        """
        self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_motion)
        self._canvas.bind("<ButtonRelease-1>", self._on_button_release)

    def _on_drag_start(self, event):
        """Mémorise la position du curseur au moment du clic et démarre l'enregistrement.

        @param event Événement tkinter contenant les coordonnées du clic.
        """
        # Coordonnées du clic par rapport au coin supérieur gauche de la fenêtre
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        # Position absolue à l'écran : sert de référence pour le seuil de drag
        self._press_x = event.x_root
        self._press_y = event.y_root
        if self._on_record_start is not None:
            self._on_record_start()

    def _on_button_release(self, event):
        """Arrête l'enregistrement au relâchement du bouton gauche.

        Le rappel n'est invoqué que si le curseur n'a pas dépassé
        `_DRAG_THRESHOLD` pixels depuis le press initial : cela évite
        de terminer un enregistrement lors d'un simple déplacement de fenêtre.

        @param event Événement tkinter contenant les coordonnées du relâchement.
        """
        dx = abs(event.x_root - self._press_x)
        dy = abs(event.y_root - self._press_y)
        if dx <= _DRAG_THRESHOLD and dy <= _DRAG_THRESHOLD:
            if self._on_record_stop is not None:
                self._on_record_stop()

    def _on_drag_motion(self, event):
        """Déplace la fenêtre en suivant le mouvement de la souris.

        Calcule le décalage entre la position actuelle du curseur et la
        position mémorisée au clic initial, puis repositionne la fenêtre.

        @param event Événement tkinter contenant les coordonnées courantes du curseur.
        """
        # Position absolue du curseur à l'écran moins le décalage initial
        new_x = self.winfo_x() + (event.x - self._drag_start_x)
        new_y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{new_x}+{new_y}")

    def _quit_app(self):
        """Nettoie les ressources externes puis détruit la fenêtre.

        Invoque `_on_quit` (s'il est défini) pour annuler les threads actifs
        avant d'appeler `destroy()`, ce qui termine proprement le processus.
        """
        if self._on_quit is not None:
            self._on_quit()
        self.destroy()

    def _bind_context_menu(self):
        """Attache l'événement clic droit pour afficher le menu contextuel."""
        self._canvas.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        """Affiche un menu contextuel avec l'entrée « Quitter ».

        @param event Événement tkinter contenant les coordonnées du clic droit.
        """
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Quitter", command=self._quit_app)
        # Affiche le menu à la position absolue du curseur sur l'écran
        menu.tk_popup(event.x_root, event.y_root)

    def _draw_mic_icon(self):
        """Dessine un microphone reconnaissable sur le canvas 50x50.

        Trois primitives composent l'icône :
        - un ovale vertical  : corps du microphone
        - une ligne verticale : tige reliant le corps à la base
        - une ligne horizontale : pied de la base
        """
        # Corps du micro : ovale centré horizontalement, tiers supérieur du canvas
        self._canvas.create_oval(
            17, 4, 33, 28,
            fill=_MIC_FILL_COLOR,
            outline=_MIC_OUTLINE_COLOR,
            width=2,
        )
        # Arc ouvert vers le bas symbolisant le col du microphone
        self._canvas.create_arc(
            10, 18, 40, 38,
            start=0, extent=-180,
            style=tk.ARC,
            outline=_MIC_OUTLINE_COLOR,
            width=2,
        )
        # Tige verticale reliant le col à la base
        self._canvas.create_line(
            25, 37, 25, 44,
            fill=_MIC_OUTLINE_COLOR,
            width=2,
        )
        # Pied horizontal de la base
        self._canvas.create_line(
            17, 44, 33, 44,
            fill=_MIC_OUTLINE_COLOR,
            width=2,
        )


if __name__ == "__main__":
    app = MicIcon()
    app.mainloop()
