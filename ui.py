"""ui.py — Composants tkinter de l'application record.

Contient :
- MicIcon : fenêtre flottante représentant l'icône micro
"""

import math
import tkinter as tk
import pyperclip


# Déplacement maximal en pixels en-deçà duquel un press+release est traité
# comme un clic d'enregistrement plutôt que comme un drag de la fenêtre
_DRAG_THRESHOLD = 5

# Couleur de fond de la bulle de texte
_BUBBLE_BG = "#2b2b2b"
# Couleur du texte de la bulle
_BUBBLE_FG = "#f0f0f0"
# Marge intérieure du label et des boutons dans la bulle
_BUBBLE_PADDING = 8
# Largeur maximale du texte dans la bulle avant retour à la ligne
_BUBBLE_MAX_WIDTH = 320

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

    def __init__(self, on_record_start=None, on_record_stop=None, on_record_cancel=None, on_quit=None):
        """Initialise la fenêtre et dessine l'icône micro.

        @param on_record_start  {callable|None} Rappel invoqué au moment où le
               bouton gauche de la souris est pressé (début d'enregistrement).
               Ignoré si None.
        @param on_record_stop   {callable|None} Rappel invoqué au moment où le
               bouton gauche de la souris est relâché (fin d'enregistrement).
               Ignoré si None.
        @param on_record_cancel {callable|None} Rappel invoqué quand un
               enregistrement démarré est annulé parce que l'utilisateur
               glisse la fenêtre au-delà de `_DRAG_THRESHOLD`. Ignoré si None.
        @param on_quit          {callable|None} Rappel invoqué juste avant la
               destruction de la fenêtre (nettoyage des threads/ressources).
               Ignoré si None.
        """
        super().__init__()
        self._on_record_start = on_record_start
        self._on_record_stop = on_record_stop
        self._on_record_cancel = on_record_cancel
        self._on_quit = on_quit
        # Vrai entre un ButtonPress-1 et le ButtonRelease-1 correspondant,
        # sauf si un drag a dépassé _DRAG_THRESHOLD (auquel cas il redevient False)
        self._recording_active = False
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
        # Référence vers la bulle de texte courante ; None si aucune n'est ouverte
        self._bubble = None
        # Identifiant retourné par self.after() pour l'animation pulsante ;
        # None quand aucune animation n'est en cours
        self._anim_after_id = None
        # Compteur de phase pour le calcul du rayon oscillant (en radians)
        self._anim_step = 0

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
        self._recording_active = True

    def _on_button_release(self, event):
        """Arrête l'enregistrement au relâchement du bouton gauche.

        Le rappel n'est invoqué que si `_recording_active` est True, c'est-
        à-dire si aucun drag dépassant `_DRAG_THRESHOLD` n'a annulé
        l'enregistrement en cours.

        @param event Événement tkinter contenant les coordonnées du relâchement.
        """
        if self._recording_active:
            self._recording_active = False
            if self._on_record_stop is not None:
                self._on_record_stop()

    def _on_drag_motion(self, event):
        """Déplace la fenêtre en suivant le mouvement de la souris.

        Calcule le décalage entre la position actuelle du curseur et la
        position mémorisée au clic initial, puis repositionne la fenêtre.
        Si le déplacement total dépasse `_DRAG_THRESHOLD` et qu'un
        enregistrement est actif, il est annulé immédiatement.

        @param event Événement tkinter contenant les coordonnées courantes du curseur.
        """
        # Annuler l'enregistrement dès que le seuil de drag est dépassé
        if self._recording_active:
            dx = abs(event.x_root - self._press_x)
            dy = abs(event.y_root - self._press_y)
            if dx > _DRAG_THRESHOLD or dy > _DRAG_THRESHOLD:
                self._recording_active = False
                if self._on_record_cancel is not None:
                    self._on_record_cancel()

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

    def start_animation(self):
        """Lance l'animation pulsante sur l'icône micro.

        Dessine un ovale rouge (tag "pulse") centré en (25, 25) dont le rayon
        oscille entre 22 et 26 px à une fréquence d'environ 120 ms par frame.
        Chaque appel planifie le suivant via `self.after` et stocke l'identifiant
        dans `_anim_after_id`. L'appel est idempotent : si une animation est déjà
        active, le comportement reste cohérent car `_anim_step` continue
        naturellement.

        @note N'a aucun effet secondaire si `stop_animation()` est appelé entre
              deux frames ; le rappel planifié est simplement annulé.
        """
        if self._anim_after_id is not None:
            return
        # Rayon oscillant : centre 24px, amplitude 2px, période ≈ 10 frames
        radius = 24 + 2 * math.sin(self._anim_step * (2 * math.pi / 10))
        cx, cy = 25, 25
        self._canvas.delete("pulse")
        self._canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            fill="#e05050",
            outline="",
            tags="pulse",
        )
        self._anim_step += 1
        self._anim_after_id = self.after(120, self.start_animation)

    def stop_animation(self):
        """Arrête l'animation pulsante et nettoie le canvas.

        Annule le rappel `after` en cours s'il existe, supprime l'ovale
        portant le tag "pulse" du canvas, puis remet `_anim_after_id` à None.
        Sans effet si aucune animation n'est active.
        """
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None
            self._canvas.delete("pulse")
            self._anim_step = 0

    def show_bubble(self, text):
        """Affiche une bulle de texte sous l'icône micro.

        Garantit qu'une seule `TextBubble` existe à la fois : si une bulle
        est déjà ouverte, elle est détruite avant d'en créer une nouvelle.

        @param text {str} Texte à afficher dans la bulle.
        """
        if self._bubble is not None and self._bubble.winfo_exists():
            self._bubble.destroy()
        self._bubble = TextBubble(self, text)


class TextBubble(tk.Toplevel):
    """Bulle de texte flottante affichant un message avec boutons Copier/Fermer.

    Fenêtre sans bordure, toujours au premier plan, positionnée sous
    la fenêtre parente (ou au-dessus si l'espace est insuffisant en bas).
    """

    def __init__(self, parent, text):
        """Initialise la bulle, construit les widgets et la positionne.

        @param parent {tk.Tk} Fenêtre parente servant d'ancre de positionnement.
        @param text   {str}   Texte à afficher dans la bulle.
        """
        super().__init__(parent)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg=_BUBBLE_BG)

        # Label affichant le texte transcrit avec retour à la ligne automatique
        tk.Label(
            self,
            text=text,
            wraplength=_BUBBLE_MAX_WIDTH,
            justify="left",
            fg=_BUBBLE_FG,
            bg=_BUBBLE_BG,
            padx=_BUBBLE_PADDING,
            pady=_BUBBLE_PADDING,
        ).pack()

        # Barre de boutons : Copier et Fermer
        btn_frame = tk.Frame(self, bg=_BUBBLE_BG)
        tk.Button(
            btn_frame,
            text="Copier",
            command=lambda: self._copy(text),
        ).pack(side="left", padx=_BUBBLE_PADDING, pady=_BUBBLE_PADDING)
        tk.Button(
            btn_frame,
            text="X",
            command=self._close,
        ).pack(side="left", padx=_BUBBLE_PADDING, pady=_BUBBLE_PADDING)
        btn_frame.pack()

        self._place(parent)

    def _copy(self, text):
        """Copie le texte de la bulle dans le presse-papiers.

        @param text {str} Texte à copier.
        """
        try:
            pyperclip.copy(text)
        except pyperclip.PyperclipException:
            pass

    def _close(self):
        """Ferme et détruit la bulle de texte."""
        self.destroy()
        if hasattr(self.master, '_bubble'):
            self.master._bubble = None

    def _place(self, parent):
        """Positionne la bulle sous la fenêtre parente, ou au-dessus si nécessaire.

        Calcule la position absolue à partir des coordonnées et dimensions
        de la fenêtre parente. Si la bulle déborde en bas de l'écran, elle
        est repositionnée au-dessus de la fenêtre parente.

        @param parent {tk.Tk} Fenêtre parente servant d'ancre de positionnement.
        """
        self.update_idletasks()
        x = parent.winfo_x()
        y = parent.winfo_y() + parent.winfo_height() + 4
        # Repositionner au-dessus si la bulle dépasse le bord inférieur de l'écran
        if y + self.winfo_reqheight() > self.winfo_screenheight():
            y = parent.winfo_y() - self.winfo_reqheight() - 4
        # Contraindre x pour éviter le débordement hors du bord droit de l'écran
        x = max(0, min(x, self.winfo_screenwidth() - self.winfo_reqwidth()))
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    app = MicIcon()
    app.mainloop()
