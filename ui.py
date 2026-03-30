"""ui.py — Composants tkinter de l'application record.

Contient :
- MicIcon : fenêtre flottante représentant l'icône micro
"""

import os
import tkinter as tk
import pyperclip
from PIL import Image, ImageTk


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

# Répertoire de base pour charger les images
_BASE = os.path.dirname(os.path.abspath(__file__))
# Taille en pixels à laquelle les images micro sont affichées
_MIC_IMAGE_SIZE = 27
# Facteur d'opacité de l'image "dim" pour l'animation pulsante (0.0–1.0)
_MIC_DIM_FACTOR = 0.35


def _load_mic_image(filename: str, dim: bool = False) -> ImageTk.PhotoImage:
    """Charge et redimensionne une image micro depuis images/.

    @param filename {str}  Nom du fichier PNG (ex. "micro_gris.png").
    @param dim      {bool} Si True, réduit l'opacité pour l'animation pulsante.
    @returns {ImageTk.PhotoImage} Image prête à afficher dans tkinter.
    """
    path = os.path.join(_BASE, "images", filename)
    img = Image.open(path).resize((_MIC_IMAGE_SIZE, _MIC_IMAGE_SIZE), Image.LANCZOS).convert("RGBA")
    if dim:
        r, g, b, a = img.split()
        a = a.point(lambda x: int(x * _MIC_DIM_FACTOR))
        img = Image.merge("RGBA", (r, g, b, a))
    return ImageTk.PhotoImage(img)


class MicIcon(tk.Tk):
    """Fenêtre flottante 50x50 représentant l'icône micro.

    Fenêtre sans bordure, toujours au premier plan, contenant un canvas
    avec un ovale symbolisant un microphone.
    """

    def __init__(self, on_record_start=None, on_record_stop=None, on_record_cancel=None, on_quit=None, on_voice_listen_toggle=None):
        """Initialise la fenêtre et dessine l'icône micro.

        @param on_record_start       {callable|None} Rappel invoqué au moment où le
               bouton gauche de la souris est pressé (début d'enregistrement).
               Ignoré si None.
        @param on_record_stop        {callable|None} Rappel invoqué au moment où le
               bouton gauche de la souris est relâché (fin d'enregistrement).
               Ignoré si None.
        @param on_record_cancel      {callable|None} Rappel invoqué quand un
               enregistrement démarré est annulé parce que l'utilisateur
               glisse la fenêtre au-delà de `_DRAG_THRESHOLD`. Ignoré si None.
        @param on_quit               {callable|None} Rappel invoqué juste avant la
               destruction de la fenêtre (nettoyage des threads/ressources).
               Ignoré si None.
        @param on_voice_listen_toggle {callable|None} Rappel invoqué dans le thread
               tkinter à chaque basculement de l'écoute vocale, avec la nouvelle
               valeur booléenne (True = activée, False = désactivée). Ignoré si None.
        """
        super().__init__()
        self._on_record_start = on_record_start
        self._on_record_stop = on_record_stop
        self._on_record_cancel = on_record_cancel
        self._on_quit = on_quit
        self._on_voice_listen_toggle = on_voice_listen_toggle
        # État courant de l'écoute vocale ; basculé via le menu contextuel
        self._voice_listening = False
        # Vrai entre un ButtonPress-1 et le ButtonRelease-1 correspondant,
        # sauf si un drag a dépassé _DRAG_THRESHOLD (auquel cas il redevient False)
        self._recording_active = False
        # Chargement des images micro (Pillow redimensionne, ImageTk rend compatible tkinter)
        # Les références doivent rester sur self pour éviter le garbage collection par tkinter
        self._img_gris     = _load_mic_image("micro_gris.png")
        self._img_ambre    = _load_mic_image("micro_ambre.png")
        self._img_bleu     = _load_mic_image("micro_bleu.png")
        self._img_vert     = _load_mic_image("micro_vert.png")
        self._img_vert_dim = _load_mic_image("micro_vert.png", dim=True)
        self._configure_window()
        self._canvas = self._build_canvas()
        self._draw_mic_image()
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
        # Phase booléenne pour l'animation pulsante (True=plein, False=dim)
        self._anim_phase = True
        # Vrai quand l'animation de transcription est active
        self._transcribing = False

    def _configure_window(self):
        """Configure les attributs de la fenêtre principale.

        Applique la taille fixe, supprime la bordure système et
        positionne la fenêtre toujours au premier plan.
        """
        self.resizable(False, False)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.geometry("29x29")
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 29) // 2
        y = (self.winfo_screenheight() - 29) // 2
        self.geometry(f"29x29+{x}+{y}")

    def _build_canvas(self):
        """Crée et positionne le canvas 50x50 dans la fenêtre.

        @returns {tk.Canvas} Le canvas attaché à la fenêtre.
        """
        canvas = tk.Canvas(
            self,
            width=29,
            height=29,
            highlightthickness=0,
            bg="#1a1a1a",
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
        self._set_mic_image(self._img_bleu)

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
                img = self._img_ambre if self._voice_listening else self._img_gris
                self._set_mic_image(img)

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

    def _toggle_voice_listening(self):
        """Bascule l'état de l'écoute vocale et notifie le callback.

        Inverse `_voice_listening`, met à jour l'icône via `set_listening_state()`
        puis invoque `_on_voice_listen_toggle` avec la nouvelle valeur si le
        callback est défini. Appelé exclusivement depuis le menu contextuel,
        donc toujours dans le thread tkinter.
        """
        self._voice_listening = not self._voice_listening
        self.set_listening_state(self._voice_listening)
        if self._on_voice_listen_toggle is not None:
            self._on_voice_listen_toggle(self._voice_listening)

    def _show_context_menu(self, event):
        """Affiche un menu contextuel avec les entrées « Écoute vocale » et « Quitter ».

        L'entrée « Écoute vocale » reflète l'état courant (`_voice_listening`) et
        bascule celui-ci au clic via `_toggle_voice_listening()`.

        @param event Événement tkinter contenant les coordonnées du clic droit.
        """
        listen_label = (
            "Écoute vocale : ON" if self._voice_listening else "Écoute vocale : OFF"
        )
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=listen_label, command=self._toggle_voice_listening)
        menu.add_command(label="Quitter", command=self._quit_app)
        # Affiche le menu à la position absolue du curseur sur l'écran
        menu.tk_popup(event.x_root, event.y_root)

    def _draw_mic_image(self):
        """Affiche l'image micro initiale (état idle) sur le canvas."""
        self._canvas.create_image(
            29 // 2, 29 // 2,
            image=self._img_gris,
            tags="mic_img",
        )

    def _set_mic_image(self, photo):
        """Remplace l'image affichée sur le canvas.

        @param photo {ImageTk.PhotoImage} Image à afficher.
        """
        self._canvas.itemconfig("mic_img", image=photo)

    def set_listening_state(self, active: bool):
        """Bascule l'icône micro en état « listening » (écoute VAD active).

        Affiche micro_ambre lorsque `active` est True, et micro_gris lorsque
        `active` est False.

        Thread-safe : si la méthode est appelée depuis un thread autre que le
        thread tkinter principal, le changement est planifié via `self.after(0, ...)`
        pour être exécuté dans la boucle d'événements.

        @param active {bool} True pour entrer en état listening, False pour revenir
               à l'état idle.
        """
        img = self._img_ambre if active else self._img_gris
        # self._canvas n'est pas thread-safe ; on délègue à la boucle d'événements
        # si l'appel provient d'un thread secondaire
        try:
            # winfo_id() lève RuntimeError si appelé hors du thread tkinter
            self._canvas.winfo_id()
            self._set_mic_image(img)
        except RuntimeError:
            self.after(0, lambda: self._set_mic_image(img))

    def set_recording_state(self, active: bool):
        """Bascule l'icône micro en état « recording » (enregistrement en cours).

        Affiche micro_bleu lorsque `active` est True, et micro_gris lorsque
        `active` est False.

        Thread-safe : planifie le changement via `self.after(0, ...)` si appelé
        hors du thread tkinter.

        @param active {bool} True pour entrer en état recording, False pour revenir
               à l'état idle.
        """
        img = self._img_bleu if active else self._img_gris
        try:
            self._canvas.winfo_id()
            self._set_mic_image(img)
        except RuntimeError:
            self.after(0, lambda: self._set_mic_image(img))

    def set_transcribing_state(self, active: bool):
        """Bascule l'icône en état « transcription » (vert pulsant) ou retour idle.

        En mode actif : affiche micro_vert et lance une animation qui alterne
        entre l'image pleine et une version à opacité réduite toutes les 400 ms.
        En mode inactif : arrête l'animation et revient à ambre (si écoute vocale
        active) ou gris (sinon).

        Thread-safe : planifie via self.after(0, ...) si appelé hors thread tkinter.

        @param active {bool} True pour démarrer, False pour arrêter.
        """
        try:
            self._canvas.winfo_id()
            self._apply_transcribing_state(active)
        except RuntimeError:
            self.after(0, lambda: self._apply_transcribing_state(active))

    def _apply_transcribing_state(self, active: bool):
        """Applique l'état transcription dans le thread tkinter."""
        if active:
            self._transcribing = True
            self._anim_phase = True
            self._set_mic_image(self._img_vert)
            self._schedule_pulse()
        else:
            self._transcribing = False
            if self._anim_after_id is not None:
                self.after_cancel(self._anim_after_id)
                self._anim_after_id = None
            img = self._img_ambre if self._voice_listening else self._img_gris
            self._set_mic_image(img)

    def _schedule_pulse(self):
        """Planifie la prochaine frame de l'animation pulsante."""
        if not self._transcribing:
            return
        self._anim_phase = not self._anim_phase
        self._set_mic_image(self._img_vert if self._anim_phase else self._img_vert_dim)
        self._anim_after_id = self.after(400, self._schedule_pulse)

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
    """Bulle de texte flottante affichant un message avec boutons copy/close.

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

        # Barre de boutons : copy et close
        btn_frame = tk.Frame(self, bg=_BUBBLE_BG)
        tk.Button(
            btn_frame,
            text="copy",
            command=lambda: self._copy(text),
        ).pack(side="left", padx=_BUBBLE_PADDING, pady=_BUBBLE_PADDING)
        tk.Button(
            btn_frame,
            text="close",
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
