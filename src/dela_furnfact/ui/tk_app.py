"""GUI mínima para empaquetar a .exe."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import json

from dela_furnfact.application import FurnFactApplicationService
from dela_furnfact.exporters import JsonExporter
from dela_furnfact.models import ContentType, LayoutMode, OpeningRequest, RemainingDistribution, ShelfRequest
from dela_furnfact.validation import parse_request_dict


class FurnFactApp:
    """Configurador de estanterías."""

    def __init__(self) -> None:
        self.service = FurnFactApplicationService()
        self.root = tk.Tk()
        self.root.title("dela-furnfact")
        self.root.geometry("1100x760")
        self.root.minsize(1024, 720)

        self.name_var = tk.StringVar(value="Estantería DELA")
        self.width_var = tk.StringVar(value="1636")
        self.height_var = tk.StringVar(value="2000")
        self.depth_var = tk.StringVar(value="300")
        self.board_var = tk.StringVar(value="18")
        self.back_var = tk.StringVar(value="5")
        self.quantity_var = tk.StringVar(value="220")
        self.kerf_var = tk.StringVar(value="3")
        self.content_var = tk.StringVar(value=ContentType.BOOKS.value)
        self.mode_var = tk.StringVar(value=LayoutMode.BALANCED.value)
        self.distribution_var = tk.StringVar(value=RemainingDistribution.UNIFORM.value)
        self.columns_var = tk.StringVar(value="")
        self.rows_var = tk.StringVar(value="")
        self.auto_fill_var = tk.BooleanVar(value=True)
        self.back_panel_var = tk.BooleanVar(value=True)
        self.split_back_var = tk.BooleanVar(value=True)
        self.center_divider_var = tk.BooleanVar(value=True)

        self.openings: list[dict] = []

        self._build()
        self._seed_demo()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        left = ttk.Frame(frame)
        right = ttk.Frame(frame)
        left.pack(side="left", fill="y")
        right.pack(side="right", fill="both", expand=True)

        form = ttk.LabelFrame(left, text="Configuración")
        form.pack(fill="x", padx=4, pady=4)

        rows = [
            ("Nombre", self.name_var),
            ("Ancho mm", self.width_var),
            ("Alto mm", self.height_var),
            ("Fondo mm", self.depth_var),
            ("Grosor tablero", self.board_var),
            ("Grosor trasera", self.back_var),
            ("Cantidad aprox.", self.quantity_var),
            ("Kerf mm", self.kerf_var),
            ("Columnas fijas", self.columns_var),
            ("Filas fijas", self.rows_var),
        ]

        for index, (label, variable) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=index, column=0, sticky="w", padx=6, pady=4)
            ttk.Entry(form, textvariable=variable, width=18).grid(row=index, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(form, text="Contenido").grid(row=10, column=0, sticky="w", padx=6, pady=4)
        ttk.Combobox(
            form,
            textvariable=self.content_var,
            state="readonly",
            values=[item.value for item in ContentType],
            width=16,
        ).grid(row=10, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(form, text="Modo layout").grid(row=11, column=0, sticky="w", padx=6, pady=4)
        ttk.Combobox(
            form,
            textvariable=self.mode_var,
            state="readonly",
            values=[item.value for item in LayoutMode],
            width=16,
        ).grid(row=11, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(form, text="Distribución sobrante").grid(row=12, column=0, sticky="w", padx=6, pady=4)
        ttk.Combobox(
            form,
            textvariable=self.distribution_var,
            state="readonly",
            values=[item.value for item in RemainingDistribution],
            width=16,
        ).grid(row=12, column=1, sticky="ew", padx=6, pady=4)

        ttk.Checkbutton(form, text="Auto-fill huecos", variable=self.auto_fill_var).grid(row=13, column=0, columnspan=2, sticky="w", padx=6, pady=4)
        ttk.Checkbutton(form, text="Trasera", variable=self.back_panel_var).grid(row=14, column=0, columnspan=2, sticky="w", padx=6, pady=2)
        ttk.Checkbutton(form, text="Trasera partida", variable=self.split_back_var).grid(row=15, column=0, columnspan=2, sticky="w", padx=6, pady=2)
        ttk.Checkbutton(form, text="Preferir divisor central", variable=self.center_divider_var).grid(row=16, column=0, columnspan=2, sticky="w", padx=6, pady=2)

        form.columnconfigure(1, weight=1)

        opening_frame = ttk.LabelFrame(left, text="Huecos pedidos")
        opening_frame.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree = ttk.Treeview(
            opening_frame,
            columns=("label", "count", "min_height", "pref_height", "max_height", "min_width", "priority", "fixed"),
            show="headings",
            height=14,
        )
        for column, heading, width in [
            ("label", "Label", 110),
            ("count", "Count", 55),
            ("min_height", "Min H", 65),
            ("pref_height", "Pref H", 65),
            ("max_height", "Max H", 65),
            ("min_width", "Min W", 65),
            ("priority", "Pri", 45),
            ("fixed", "Fijo", 50),
        ]:
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, stretch=True)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        add_bar = ttk.Frame(opening_frame)
        add_bar.pack(fill="x", padx=6, pady=6)

        self.opening_label_var = tk.StringVar(value="books_large")
        self.opening_count_var = tk.StringVar(value="1")
        self.opening_min_height_var = tk.StringVar(value="249")
        self.opening_pref_height_var = tk.StringVar(value="249")
        self.opening_max_height_var = tk.StringVar(value="")
        self.opening_min_width_var = tk.StringVar(value="0")
        self.opening_priority_var = tk.StringVar(value="3")
        self.opening_fixed_var = tk.BooleanVar(value=False)

        for text, variable, width in [
            ("Label", self.opening_label_var, 14),
            ("Count", self.opening_count_var, 5),
            ("Min H", self.opening_min_height_var, 7),
            ("Pref H", self.opening_pref_height_var, 7),
            ("Max H", self.opening_max_height_var, 7),
            ("Min W", self.opening_min_width_var, 7),
            ("Pri", self.opening_priority_var, 4),
        ]:
            ttk.Label(add_bar, text=text).pack(side="left", padx=3)
            ttk.Entry(add_bar, textvariable=variable, width=width).pack(side="left", padx=3)

        ttk.Checkbutton(add_bar, text="Fijo", variable=self.opening_fixed_var).pack(side="left", padx=4)
        ttk.Button(add_bar, text="Añadir", command=self._add_opening).pack(side="left", padx=6)
        ttk.Button(add_bar, text="Eliminar", command=self._remove_selected_opening).pack(side="left", padx=6)

        buttons = ttk.Frame(left)
        buttons.pack(fill="x", padx=4, pady=4)
        ttk.Button(buttons, text="Cargar JSON", command=self._load_json).pack(side="left", padx=4)
        ttk.Button(buttons, text="Generar", command=self._generate).pack(side="left", padx=4)
        ttk.Button(buttons, text="Exportar bundle", command=self._export_bundle).pack(side="left", padx=4)

        output = ttk.LabelFrame(right, text="Resultado")
        output.pack(fill="both", expand=True, padx=4, pady=4)

        self.output_text = tk.Text(output, wrap="word", font=("Consolas", 11))
        self.output_text.pack(fill="both", expand=True, padx=6, pady=6)

    def _seed_demo(self) -> None:
        self.openings = [
            {"label": "books_large", "count": 1, "min_clear_height_mm": 249.0, "preferred_clear_height_mm": 249.0, "min_clear_width_mm": 0.0},
            {"label": "books_small", "count": 2, "min_clear_height_mm": 210.0, "preferred_clear_height_mm": 210.0, "min_clear_width_mm": 0.0},
            {"label": "books_large", "count": 2, "min_clear_height_mm": 249.0, "preferred_clear_height_mm": 249.0, "min_clear_width_mm": 0.0},
            {"label": "books_small", "count": 2, "min_clear_height_mm": 211.0, "preferred_clear_height_mm": 211.0, "min_clear_width_mm": 0.0},
            {"label": "books_large", "count": 1, "min_clear_height_mm": 249.0, "preferred_clear_height_mm": 249.0, "min_clear_width_mm": 0.0},
        ]
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for opening in self.openings:
            self.tree.insert(
                "",
                "end",
                values=(
                    opening["label"],
                    opening["count"],
                    opening["min_clear_height_mm"],
                    opening.get("preferred_clear_height_mm", ""),
                    opening.get("max_clear_height_mm", ""),
                    opening.get("min_clear_width_mm", 0.0),
                    opening.get("priority", 3),
                    "sí" if opening.get("fixed_height", False) else "no",
                ),
            )

    def _add_opening(self) -> None:
        try:
            preferred_height = self.opening_pref_height_var.get().strip()
            max_height = self.opening_max_height_var.get().strip()
            item = {
                "label": self.opening_label_var.get().strip(),
                "count": int(self.opening_count_var.get()),
                "min_clear_height_mm": float(self.opening_min_height_var.get()),
                "preferred_clear_height_mm": None if not preferred_height else float(preferred_height),
                "max_clear_height_mm": None if not max_height else float(max_height),
                "min_clear_width_mm": float(self.opening_min_width_var.get()),
                "priority": int(self.opening_priority_var.get()),
                "fixed_height": self.opening_fixed_var.get(),
            }
            if not item["label"]:
                raise ValueError("El label no puede estar vacío.")
            self.openings.append(item)
            self._refresh_tree()
        except ValueError as exc:
            messagebox.showerror("Hueco inválido", str(exc))

    def _remove_selected_opening(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        del self.openings[index]
        self._refresh_tree()

    def _request_payload(self) -> dict:
        def optional_int(value: str) -> int | None:
            value = value.strip()
            return None if not value else int(value)

        return {
            "name": self.name_var.get(),
            "width_mm": float(self.width_var.get()),
            "height_mm": float(self.height_var.get()),
            "depth_mm": float(self.depth_var.get()),
            "board_thickness_mm": float(self.board_var.get()),
            "back_panel_thickness_mm": float(self.back_var.get()),
            "content_type": self.content_var.get(),
            "content_quantity": int(self.quantity_var.get()),
            "layout_mode": self.mode_var.get(),
            "remaining_distribution": self.distribution_var.get(),
            "has_back_panel": self.back_panel_var.get(),
            "split_back_panel": self.split_back_var.get(),
            "has_center_divider": self.center_divider_var.get(),
            "kerf_mm": float(self.kerf_var.get()),
            "units": "mm",
            "fixed_columns": optional_int(self.columns_var.get()),
            "fixed_rows": optional_int(self.rows_var.get()),
            "allow_auto_fill": self.auto_fill_var.get(),
            "requested_openings": self.openings,
        }

    def _generate(self) -> None:
        try:
            request = parse_request_dict(self._request_payload())
            bundle = self.service.generate(request)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "\n".join(bundle.summary_lines()))
        self.output_text.insert("end", "\n\nHuecos:\n")
        for opening in bundle.plan.openings:
            self.output_text.insert(
                "end",
                (
                    f"- #{opening.index} {opening.label}: "
                    f"{opening.clear_height_mm:.1f}h x {opening.clear_width_mm:.1f}w x "
                    f"{opening.clear_depth_mm:.1f}d mm [{opening.source}]\n"
                ),
            )
        self.last_bundle = bundle

    def _export_bundle(self) -> None:
        bundle = getattr(self, "last_bundle", None)
        if bundle is None:
            self._generate()
            bundle = getattr(self, "last_bundle", None)
        if bundle is None:
            return

        path = filedialog.asksaveasfilename(
            title="Guardar bundle",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        JsonExporter().write(bundle, Path(path))
        messagebox.showinfo("Exportado", f"Bundle guardado en:\n{path}")

    def _load_json(self) -> None:
        path = filedialog.askopenfilename(
            title="Abrir request JSON",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            request = parse_request_dict(payload)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.name_var.set(request.name)
        self.width_var.set(str(request.width_mm))
        self.height_var.set(str(request.height_mm))
        self.depth_var.set(str(request.depth_mm))
        self.board_var.set(str(request.board_thickness_mm))
        self.back_var.set(str(request.back_panel_thickness_mm))
        self.quantity_var.set(str(request.content_quantity))
        self.kerf_var.set(str(request.kerf_mm))
        self.content_var.set(request.content_type.value)
        self.mode_var.set(request.layout_mode.value)
        self.distribution_var.set(request.remaining_distribution.value)
        self.columns_var.set("" if request.fixed_columns is None else str(request.fixed_columns))
        self.rows_var.set("" if request.fixed_rows is None else str(request.fixed_rows))
        self.auto_fill_var.set(request.allow_auto_fill)
        self.back_panel_var.set(request.has_back_panel)
        self.split_back_var.set(request.split_back_panel)
        self.center_divider_var.set(request.has_center_divider)

        self.openings = [
            {
                "label": item.label,
                "count": item.count,
                "min_clear_height_mm": item.min_clear_height_mm,
                "preferred_clear_height_mm": item.preferred_clear_height_mm,
                "min_clear_width_mm": item.min_clear_width_mm,
            }
            for item in request.requested_openings
        ]
        self._refresh_tree()

    def run(self) -> None:
        self.root.mainloop()


def launch_gui() -> None:
    FurnFactApp().run()
