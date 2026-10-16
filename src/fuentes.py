"""Lectores de archivos CSV y JSON para las mediciones."""

from abc import ABC, abstractmethod
import csv
import json


class FuenteDatos(ABC):
    """Interfaz común para las fuentes de registros."""

    @abstractmethod
    def cargar(self, ruta):
        """Lee una ruta y devuelve una lista de registros."""
        raise NotImplementedError


class FuenteCSV(FuenteDatos):
    """Fuente de registros CSV."""

    def cargar(self, ruta):
        with open(ruta, encoding="utf-8", newline="") as archivo:
            return list(csv.DictReader(archivo))


class FuenteJSON(FuenteDatos):
    """Fuente de registros JSON."""

    def cargar(self, ruta):
        with open(ruta, encoding="utf-8") as archivo:
            registros = json.load(archivo)

        if not isinstance(registros, list):
            raise ValueError("El contenido JSON debe ser una lista de registros.")

        return registros
