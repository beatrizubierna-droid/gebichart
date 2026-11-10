"""Validación local: los recursos originales se han copiado sin alterar bytes."""
from pathlib import Path
import hashlib, sys

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def verify(original, destino):
    failures=[]; count=0
    for f in original.rglob('*'):
        if f.is_file():
            rel=f.relative_to(original); target=destino/rel; count+=1
            if not target.is_file(): failures.append(f'FALTA: {rel}')
            elif sha(f)!=sha(target): failures.append(f'MODIFICADO: {rel}')
    print(f'{count} archivos originales comprobados; {len(failures)} diferencias')
    print('\n'.join(failures))
    return not failures

if __name__=='__main__':
    if len(sys.argv)!=3:
        print('Uso: python validar_recursos.py ruta_original_static_gebichart ruta_django_static_gebichart')
        sys.exit(2)
    sys.exit(0 if verify(Path(sys.argv[1]),Path(sys.argv[2])) else 1)
