from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
import os
from datetime import datetime
from collections import Counter

print("--- Iniciando la aplicación Flask en Heroku ---")

try:
    app = Flask(__name__)
    print("--- Iniciando la aplicación Flask en Heroku - Flask App Creada ---")
except Exception as e:
    print(f"--- Iniciando la aplicación Flask en Heroku - Error al crear la aplicación Flask: {e} ---")
    raise  # Esto hará que la aplicación falle y Heroku lo registre

app.secret_key = os.environ.get('SECRET_KEY', 'tu_clave_secreta')  # Usar variable de entorno para la clave secreta

# Datos del administrador - ¡IMPORTANTE! Usar variables de entorno para información sensible
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'nuzja')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'golum')
EXCEL_FILENAME = os.environ.get('EXCEL_FILENAME', 'solicitudes.xlsx')

print("--- Iniciando la aplicación Flask en Heroku - Verificando archivo Excel ---")
try:
    if not os.path.exists(EXCEL_FILENAME):
        print(f"--- Iniciando la aplicación Flask en Heroku - Archivo Excel no encontrado, creando: {EXCEL_FILENAME} ---")
        df = pd.DataFrame(columns=['Nombre', 'Apellido', 'RUT', 'Email', 'Teléfono Movil', 'Ingreso Bruto (CLP)', 'Clínicas de Preferencia', '¿Tienes Seguro Complementario?', 'Fecha de Ingreso', 'Estado'])
        df.to_excel(EXCEL_FILENAME, index=False)
        print("--- Iniciando la aplicación Flask en Heroku - Archivo Excel creado ---")
    else:
        print(f"--- Iniciando la aplicación Flask en Heroku - Archivo Excel encontrado, leyendo: {EXCEL_FILENAME} ---")
        try:
            df = pd.read_excel(EXCEL_FILENAME)
            print("--- Iniciando la aplicación Flask en Heroku - Archivo Excel leído ---")
            # Añadir nuevas columnas si no existen
            if 'Fecha de Ingreso' not in df.columns:
                print("--- Iniciando la aplicación Flask en Heroku - Columna 'Fecha de Ingreso' no encontrada, agregando ---")
                df['Fecha de Ingreso'] = None
                df.to_excel(EXCEL_FILENAME, index=False)
                print("--- Iniciando la aplicación Flask en Heroku - Columna 'Fecha de Ingreso' agregada ---")
            if 'Estado' not in df.columns:
                print("--- Iniciando la aplicación Flask en Heroku - Columna 'Estado' no encontrada, agregando ---")
                df['Estado'] = 'Pendiente'  # Estado inicial
                df.to_excel(EXCEL_FILENAME, index=False)
                print("--- Iniciando la aplicación Flask en Heroku - Columna 'Estado' agregada ---")
        except Exception as inner_e:
            print(f"--- Iniciando la aplicación Flask en Heroku - Error específico al leer o actualizar el archivo Excel: {inner_e} ---")
            raise
except Exception as outer_e:
    print(f"--- Iniciando la aplicación Flask en Heroku - Error general al verificar el archivo Excel: {outer_e} ---")
    raise # Esto hará que la aplicación falle y Heroku lo registre

def calcular_7_porciento(ingreso_bruto):
    try:
        # Eliminar puntos y convertir a float
        ingreso = float(str(ingreso_bruto).replace('.', ''))
        return ingreso * 0.07
    except ValueError:
        return "Error: Ingreso no válido"

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        rut = request.form.get('rut')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        ingreso_bruto = request.form.get('ingreso_bruto')
        clinicas = ', '.join(request.form.getlist('clinicas'))
        seguro_complementario = request.form.get('seguro_complementario')

        porcentaje_7 = calcular_7_porciento(ingreso_bruto)
        fecha_ingreso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        estado = 'Pendiente'

        nueva_fila = pd.DataFrame([{'Nombre': nombre, 'Apellido': apellido, 'RUT': rut, 'Email': email, 'Teléfono Movil': telefono, 'Ingreso Bruto (CLP)': ingreso_bruto, 'Clínicas de Preferencia': clinicas, '¿Tienes Seguro Complementario?': seguro_complementario, 'Fecha de Ingreso': fecha_ingreso, 'Estado': estado}])

        try:
            df = pd.read_excel(EXCEL_FILENAME)
            df = pd.concat([df, nueva_fila], ignore_index=True)
            df.to_excel(EXCEL_FILENAME, index=False)
            return render_template('gracias.html', porcentaje_7=porcentaje_7, ingreso_bruto=ingreso_bruto)
        except Exception as e:
            print(f"Error al guardar en Excel: {e}")
            return render_template('error.html', mensaje="Error al guardar la información.")

    return render_template('formulario.html')

@app.route('/volver_formulario')
def volver_formulario():
    return redirect(url_for('formulario'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Credenciales incorrectas')
    return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    try:
        df = pd.read_excel(EXCEL_FILENAME)
        status_counts = Counter(df['Estado'])

        monthly_income_data = {}
        if 'Fecha de Ingreso' in df.columns:
            try:
                df['Fecha de Ingreso'] = pd.to_datetime(df['Fecha de Ingreso'])
                monthly_counts = df.groupby(pd.Grouper(key='Fecha de Ingreso', freq='M')).size().to_dict()
                monthly_income_data = {date.strftime('%Y-%m'): count for date, count in monthly_counts.items()}
            except Exception as e:
                print(f"Error al procesar la fecha de ingreso para la gráfica temporal: {e}")
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Nombre', 'Apellido', 'RUT', 'Email', 'Teléfono Movil', 'Ingreso Bruto (CLP)', 'Clínicas de Preferencia', '¿Tienes Seguro Complementario?', 'Fecha de Ingreso', 'Estado'])
        status_counts = {}

    return render_template('admin_panel.html', data=df.to_dict('records'), status_counts=status_counts, monthly_income_data=monthly_income_data)

@app.route('/admin/descargar_excel')
def descargar_excel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    try:
        return send_file(EXCEL_FILENAME, as_attachment=True)
    except FileNotFoundError:
        return "No se encontró el archivo de solicitudes."

@app.route('/admin/eliminar/<int:index>')
def eliminar_fila(index):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    try:
        df = pd.read_excel(EXCEL_FILENAME)
        if 0 <= index < len(df):
            df = df.drop(index).reset_index(drop=True)
            df.to_excel(EXCEL_FILENAME, index=False)
    except FileNotFoundError:
        pass # El archivo no existe, no hay nada que eliminar
    return redirect(url_for('admin_panel'))

@app.route('/admin/editar/<int:index>', methods=['GET', 'POST'])
def editar_fila(index):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    try:
        df = pd.read_excel(EXCEL_FILENAME)
        if index < 0 or index >= len(df):
            return "Índice inválido"

        if request.method == 'POST':
            df.loc[index, 'Nombre'] = request.form.get('nombre')
            df.loc[index, 'Apellido'] = request.form.get('apellido')
            df.loc[index, 'RUT'] = request.form.get('rut')
            df.loc[index, 'Email'] = request.form.get('email')
            df.loc[index, 'Teléfono Movil'] = request.form.get('telefono')
            df.loc[index, 'Ingreso Bruto (CLP)'] = request.form.get('ingreso_bruto')
            df.loc[index, 'Clínicas de Preferencia'] = ', '.join(request.form.getlist('clinicas'))
            df.loc[index, '¿Tienes Seguro Complementario?'] = request.form.get('seguro_complementario')
            df.to_excel(EXCEL_FILENAME, index=False)
            return redirect(url_for('admin_panel'))
        else:
            fila = df.iloc[index].to_dict()
            fila['Clínicas de Preferencia'] = fila.get('Clínicas de Preferencia', '').split(', ')
            return render_template('editar_fila.html', index=index, fila=fila, clinicas=['Clínica Alemana', 'U Andes', 'UC Christus', 'Indisa', 'Clínica Santa María', 'Red Salud', 'Meds'])
    except FileNotFoundError:
        return "No se encontró el archivo de solicitudes."

@app.route('/admin/actualizar_estado/<int:index>', methods=['POST'])
def actualizar_estado(index):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in ['Pendiente', 'Rechazado', 'Cerrado']:
        try:
            df = pd.read_excel(EXCEL_FILENAME)
            if 0 <= index < len(df):
                df.loc[index, 'Estado'] = nuevo_estado
                df.to_excel(EXCEL_FILENAME, index=False)
                return {'success': True, 'estado': nuevo_estado}
            else:
                return {'success': False, 'error': 'Índice inválido'}, 400
        except FileNotFoundError:
            return {'success': False, 'error': 'Archivo de solicitudes no encontrado'}, 404
    else:
        return {'success': False, 'error': 'Estado inválido'}, 400

# ¡LA SIGUIENTE LÍNEA DEBE ESTAR COMENTADA PARA DESPLEGAR EN HEROKU!
# if __name__ == '__main__':
#     app.run(debug=True) analizalo bien porfavor
