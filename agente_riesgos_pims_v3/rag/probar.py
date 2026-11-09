"""Prueba del buscador documental."""
import sys
from rag.recuperar_contexto import recuperar_contexto_rag

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "acceso no autorizado a datos personales"
    r = recuperar_contexto_rag(q)
    print("Estado:", r["estado"], r["mensaje"])
    for f in r["fragmentos"]:
        print(f["archivo"], "página", f["pagina"], "similitud", f["similitud"])
        print(f["texto"][:300])
