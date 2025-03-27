from flask import Flask, render_template, request, redirect, url_for, send_file, session
import pandas as pd
import os
from datetime import datetime
from collections import Counter

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # ¡Cambia esto por una clave secreta real!

# Datos del administrador (¡No uses esto en producción para información sensible!)
ADMIN_USERNAME = 'nuzja'
ADMIN_PASSWORD = 'golum'
EXCEL_FILENAME = 'solicitudes.xlsx'

# Asegurarse de que el archivo Excel exista y tenga las nuevas columnas
if not os.path.exists(EXCEL_FILENAME):
    df = pd.DataFrame(columns=['Nombre', 'Apellido', 'RUT', 'Email', 'Teléfono Movil', 'Ingreso Bruto (CLP)', 'Clínicas de Preferencia', '¿Tienes Seguro Complementario?', 'Fecha de Ingreso', 'Estado'])
    df.to_excel(EXCEL_FILENAME, index=False)
else:
    df = pd.read_excel(EXCEL_FILENAME)
    if 'Fecha de Ingreso' not in df.columns:
        df['Fecha de Ingreso'] = None
        df.to_excel(EXCEL_FILENAME, index=False)
    if 'Estado' not in df.columns:
        df['Estado'] = 'Pendiente'  # Estado inicial
        df.to_excel(EXCEL_FILENAME, index=False)

def calcular_7_porciento(ingreso_bruto):
    try:
        ingreso = float(ingreso_bruto.replace('.', '')) # Eliminar puntos para convertir a número
        return ingreso * 0.07
    except ValueError:
        return "Error: Ingreso no válido"

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        rut = request.form['rut']
        email = request.form['email']
        telefono = request.form['telefono']
        ingreso_bruto = request.form['ingreso_bruto']
        clinicas = ', '.join(request.form.getlist('clinicas'))
        seguro_complementario = request.form['seguro_complementario']

        porcentaje_7 = calcular_7_porciento(ingreso_bruto)

        # Guardar en Excel con fecha de ingreso y estado inicial
        df = pd.read_excel(EXCEL_FILENAME)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nueva_fila = pd.DataFrame([{'Nombre': nombre, 'Apellido': apellido, 'RUT': rut, 'Email': email, 'Teléfono Movil': telefono, 'Ingreso Bruto (CLP)': ingreso_bruto, 'Clínicas de Preferencia': clinicas, '¿Tienes Seguro Complementario?': seguro_complementario, 'Fecha de Ingreso': now, 'Estado': 'Pendiente'}])
        df = pd.concat([df, nueva_fila], ignore_index=True)
        df.to_excel(EXCEL_FILENAME, index=False)

        return render_template('gracias.html', porcentaje_7=porcentaje_7, ingreso_bruto=ingreso_bruto)
    return render_template('formulario.html')

@app.route('/volver_formulario')
def volver_formulario():
    return redirect(url_for('formulario'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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
    df = pd.read_excel(EXCEL_FILENAME)

    # Gráfica de torta por estado
    status_counts = Counter(df['Estado'])

    # Gráfica de línea temporal por mes
    if 'Fecha de Ingreso' in df.columns:
        try:
            df['Fecha de Ingreso'] = pd.to_datetime(df['Fecha de Ingreso'])
            monthly_counts = df.groupby(pd.Grouper(key='Fecha de Ingreso', freq='M')).size().to_dict()
            # Formatear las claves del diccionario para que sean strings mes-año
            monthly_income_data = {date.strftime('%Y-%m'): count for date, count in monthly_counts.items()}
        except Exception as e:
            print(f"Error al procesar la fecha de ingreso para la gráfica temporal: {e}")
            monthly_income_data = {}
    else:
        monthly_income_data = {}

    return render_template('admin_panel.html', data=df.to_dict('records'), status_counts=status_counts, monthly_income_data=monthly_income_data)

@app.route('/admin/descargar_excel')
def descargar_excel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return send_file(EXCEL_FILENAME, as_attachment=True)

@app.route('/admin/eliminar/<int:index>')
def eliminar_fila(index):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    df = pd.read_excel(EXCEL_FILENAME)
    if 0 <= index < len(df):
        df = df.drop(index)
        df.reset_index(drop=True, inplace=True)
        df.to_excel(EXCEL_FILENAME, index=False)
    return redirect(url_for('admin_panel'))

@app.route('/admin/editar/<int:index>', methods=['GET', 'POST'])
def editar_fila(index):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    df = pd.read_excel(EXCEL_FILENAME)
    if index < 0 or index >= len(df):
        return "Índice inválido"

    if request.method == 'POST':
        df.loc[index, 'Nombre'] = request.form['nombre']
        df.loc[index, 'Apellido'] = request.form['apellido']
        df.loc[index, 'RUT'] = request.form['rut']
        df.loc[index, 'Email'] = request.form['email']
        df.loc[index, 'Teléfono Movil'] = request.form['telefono']
        df.loc[index, 'Ingreso Bruto (CLP)'] = request.form['ingreso_bruto']
        df.loc[index, 'Clínicas de Preferencia'] = ', '.join(request.form.getlist('clinicas'))
        df.loc[index, '¿Tienes Seguro Complementario?'] = request.form['seguro_complementario']
        df.to_excel(EXCEL_FILENAME, index=False)
        return redirect(url_for('admin_panel'))
    else:
        fila = df.iloc[index].to_dict()
        fila['Clínicas de Preferencia'] = fila['Clínicas de Preferencia'].split(', ') if isinstance(fila['Clínicas de Preferencia'], str) else []
        return render_template('editar_fila.html', index=index, fila=fila, clinicas=['Clínica Alemana', 'U Andes', 'UC Christus', 'Indisa', 'Clínica Santa María', 'Red Salud', 'Meds'])

@app.route('/admin/actualizar_estado/<int:index>', methods=['POST'])
def actualizar_estado(index):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in ['Pendiente', 'Rechazado', 'Cerrado']:
        df = pd.read_excel(EXCEL_FILENAME)
        if 0 <= index < len(df):
            df.loc[index, 'Estado'] = nuevo_estado
            df.to_excel(EXCEL_FILENAME, index=False)
            return {'success': True, 'estado': nuevo_estado}
        else:
            return {'success': False, 'error': 'Índice inválido'}, 400
    else:
        return {'success': False, 'error': 'Estado inválido'}, 400

if __name__ == '__main__':
    app.run(debug=True)