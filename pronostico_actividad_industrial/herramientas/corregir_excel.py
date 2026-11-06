"""Aplica las correcciones aprobadas a base_imai.xlsx editando el XML del paquete.

Se edita el XML (no openpyxl) para conservar conexiones de datos, consultas y
vínculos externos del libro. Cambios:
  1. CONST!X224:X406 (SHCP1, 2011-07 a 2026-09): ='SHCP REAL'!B{fila+1}.
  2. ELEC: se insertan 54 filas (1993-01 a 1997-06) con fórmulas a IMAI!D,
     CFE!B:H e INPP!E (desde 1994-01); IMSS y ENOE quedan vacías (no existen).
  3. Se elimina calcChain.xml (Excel lo reconstruye) y se fuerza el recálculo
     completo al abrir (fullCalcOnLoad).
Los valores en caché de las celdas nuevas o modificadas se toman de las celdas
fuente del propio libro, para que cualquier lector de valores (readxl, pandas)
vea lo mismo que Excel calculará.
"""
import re, sys, zipfile, datetime as dt
import openpyxl

origen, destino = sys.argv[1], sys.argv[2]
vals = openpyxl.load_workbook(origen, read_only=True, data_only=True)

def valor(hoja, celda):
    v = vals[hoja][celda].value
    return v

def num(v):
    return repr(float(v))

zin = zipfile.ZipFile(origen)
archivos = {i.filename: zin.read(i.filename) for i in zin.infolist()}
orden = [i.filename for i in zin.infolist()]

# ---------------------------------------------------------------- CONST (sheet19)
const = archivos['xl/worksheets/sheet19.xml'].decode('utf-8')
n_const = 0
for fila in range(224, 407):
    patron = re.compile(r'(<c r="X%d"[^>]*>)<f>\'SHCP REAL\'!C\d+</f><v>[^<]*</v>(</c>)' % fila)
    v = valor('SHCP REAL', 'B%d' % (fila + 1))
    nuevo = r"\1<f>'SHCP REAL'!B%d</f><v>%s</v>\2" % (fila + 1, num(v))
    const, k = patron.subn(nuevo, const)
    assert k == 1, ('CONST', fila)
    n_const += k
archivos['xl/worksheets/sheet19.xml'] = const.encode('utf-8')

# ---------------------------------------------------------------- ELEC (sheet21)
elec = archivos['xl/worksheets/sheet21.xml'].decode('utf-8')
N_NUEVAS = 54
ini_data = elec.index('<sheetData>') + len('<sheetData>')
fin_data = elec.index('</sheetData>')
datos = elec[ini_data:fin_data]
filas = re.findall(r'<row r="(\d+)".*?</row>|<row r="(\d+)"[^>]*/>', datos)
bloques = re.findall(r'(<row r="\d+"[^>]*?(?:/>|>.*?</row>))', datos)
assert ''.join(bloques) == datos

def desplazar(bloque):
    r = int(re.match(r'<row r="(\d+)"', bloque).group(1))
    if r == 1:
        return bloque
    nr = r + N_NUEVAS
    bloque = re.sub(r'^<row r="%d"' % r, '<row r="%d"' % nr, bloque)
    bloque = re.sub(r'<c r="([A-Z]+)%d"' % r, lambda m: '<c r="%s%d"' % (m.group(1), nr), bloque)
    return bloque

bloques = [desplazar(b) for b in bloques]
assert 'ELEC!' not in elec

nuevas = []
for k in range(N_NUEVAS):
    fecha = dt.date(1993, 1, 1).replace(year=1993 + k // 12, month=k % 12 + 1)
    serial = (fecha - dt.date(1899, 12, 30)).days
    r = 2 + k
    celdas = ['<c r="A%d" s="32"><v>%d</v></c>' % (r, serial)]
    fila_imai = 19 + k   # IMAI!19 = 1993-01
    celdas.append('<c r="B%d"><f>IMAI!D%d</f><v>%s</v></c>' % (r, fila_imai, num(valor('IMAI', 'D%d' % fila_imai))))
    for col_dest, col_cfe in zip('EFGHIJK', 'BCDEFGH'):
        fila_cfe = 19 + k  # CFE!19 = 1993-01
        celdas.append('<c r="%s%d"><f>CFE!%s%d</f><v>%s</v></c>' % (col_dest, r, col_cfe, fila_cfe, num(valor('CFE', '%s%d' % (col_cfe, fila_cfe)))))
    fila_inpp = 7 + k        # INPP!7 = 1993/01; la columna E empieza en 1994/01
    v_inpp = valor('INPP', 'E%d' % fila_inpp)
    if v_inpp is not None:
        celdas.append('<c r="L%d"><f>INPP!E%d</f><v>%s</v></c>' % (r, fila_inpp, num(v_inpp)))
    nuevas.append('<row r="%d" spans="1:13" x14ac:dyDescent="0.25">%s</row>' % (r, ''.join(celdas)))

bloques = bloques[:1] + nuevas + bloques[1:]
elec = elec[:ini_data] + ''.join(bloques) + elec[fin_data:]
elec = elec.replace('<dimension ref="A1:M358"/>', '<dimension ref="A1:M%d"/>' % (358 + N_NUEVAS))
archivos['xl/worksheets/sheet21.xml'] = elec.encode('utf-8')

# ---------------------------------------------------------------- calcChain y recálculo
del archivos['xl/calcChain.xml']; orden.remove('xl/calcChain.xml')
ct = archivos['[Content_Types].xml'].decode('utf-8')
ct, k = re.subn(r'<Override PartName="/xl/calcChain.xml"[^>]*/>', '', ct); assert k == 1
archivos['[Content_Types].xml'] = ct.encode('utf-8')
rel = archivos['xl/_rels/workbook.xml.rels'].decode('utf-8')
rel, k = re.subn(r'<Relationship [^>]*Target="calcChain.xml"[^>]*/>', '', rel); assert k == 1
archivos['xl/_rels/workbook.xml.rels'] = rel.encode('utf-8')
wbx = archivos['xl/workbook.xml'].decode('utf-8')
wbx, k = re.subn(r'<calcPr calcId="191029"/>', '<calcPr calcId="191029" fullCalcOnLoad="1"/>', wbx); assert k == 1
archivos['xl/workbook.xml'] = wbx.encode('utf-8')

with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zout:
    for nombre in orden:
        zout.writestr(nombre, archivos[nombre])
print('CONST celdas corregidas:', n_const, '| ELEC filas insertadas:', N_NUEVAS)
