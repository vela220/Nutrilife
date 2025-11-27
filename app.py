from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests

app = Flask(__name__)
app.secret_key = "clave_secreta"

API_KEY = "X6bcYYVWiKi2VhDRFij4dErDszBeJVsWRe0YFvG9"

def buscar_recetas_api(consulta):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": consulta,
        "pageSize": 10
    }

    respuesta = requests.get(url, params=params)

    if respuesta.status_code == 200:
        return respuesta.json()
    else:
        return {"foods": []}

@app.route("/api/buscar")
def api_buscar():
    consulta = request.args.get("q", "").strip()

    if not consulta:
        return jsonify([])

    datos = buscar_recetas_api(consulta)

    alimentos = []

    for f in datos.get("foods", []):
        alimentos.append({
            "id": f.get("fdcId"),
            "nombre": f.get("description", "Desconocido"),
            "tipo": f.get("dataType", "N/D")
        })

    return jsonify (alimentos)

@app.route("/api/alimento/<int:fdc_id>")
def api_alimento(fdc_id):

    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={API_KEY}"
    r = requests.get(url)

    if r.status_code != 200:
        return jsonify({"error": "No se pudo obtener información"}), 400

    data = r.json()

    
    nutrientes = {}
    for n in data.get("foodNutrients", []):
        nut = n.get("nutrient", {})
        nombre = nut.get("name")
        valor = n.get("amount", "N/D")

        if nombre:
            nutrientes[nombre] = valor

    detalle = {
        "id": fdc_id,
        "nombre": data.get("description", "N/D"),
        "tipo": data.get("dataType", "N/D"),
        "nutricion": {
            "calorias": nutrientes.get("Energy", "N/D"),
            "proteina": nutrientes.get("Protein", "N/D"),
            "grasa": nutrientes.get("Total lipid (fat)", "N/D"),
            "carbohidratos": nutrientes.get("Carbohydrate, by difference", "N/D")
        }
    }

    return jsonify(detalle)


@app.route("/")
def lobby():
    return render_template("lobby.html")

@app.route("/inicio")
def inicio():
    if not session.get("usuario"):
        return redirect(url_for("sesion"))
    return render_template("inicio.html")


@app.route("/sesion", methods=["GET", "POST"])
def sesion():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email and password:
            session["usuario"] = email
            print(f"Inicio de sesión de: {email}")
            return redirect(url_for("inicio"))
        else:
            return render_template("sesion.html", error="Datos incorrectos")

    return render_template("sesion.html")





@app.route("/formulario", methods=["GET", "POST"])
def formulario():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        email = request.form.get("email")
        password = request.form.get("password")
        genero = request.form.get("genero")
        experiencia = request.form.get("experiencia")
        objetivos = request.form.get("objetivos")
        alergias = request.form.get("alergias")
        intolerancias = request.form.get("intolerancias")
        dietas = request.form.get("dietas")
        no_gustan = request.form.get("no_gustan")

        print(f"Nuevo usuario registrado: {nombre} {apellido} ({email})")
        print(f"Género: {genero}, Experiencia: {experiencia}")
        print(f"Objetivos: {objetivos}")
        print(f"Alergias: {alergias}")
        print(f"Intolerancias: {intolerancias}")
        print(f"Dietas: {dietas}")
        print(f"No le gustan: {no_gustan}")

        return redirect(url_for("inicio"))

    return render_template("formulario.html")


@app.route("/dieta", methods=["GET", "POST"])
def dieta():
    datos_usuario = None
    dieta_generada = None

    if request.method == "POST":
        edad = int(request.form["edad"])
        peso = float(request.form["peso"])
        altura = float(request.form["altura"])
        objetivo = request.form["objetivo"]

        
        session["nutri_datos"] = {
            "edad": edad,
            "peso": peso,
            "altura": altura,
            "objetivo": objetivo
        }

        datos_usuario = session["nutri_datos"]

        
        if objetivo == "bajar":
            dieta_generada = [
                "Desayuno: Avena con manzana",
                "Comida: Pollo a la plancha con verduras",
                "Cena: Ensalada verde con atún",
                "Snack: Yogur griego"
            ]
        elif objetivo == "subir":
            dieta_generada = [
                "Desayuno: Huevos + pan integral",
                "Comida: Pasta con carne molida",
                "Cena: Sándwich de pavo",
                "Snack: Almendras"
            ]
        else:  
            dieta_generada = [
                "Desayuno: Smoothie de frutas",
                "Comida: Arroz + pollo + ensalada",
                "Cena: Wrap de vegetales",
                "Snack: Gelatina light"
            ]

    return render_template("dieta.html",
            datos=datos_usuario,
            dieta=dieta_generada)



@app.route("/horarioC", methods=["GET", "POST"])
def horario():
    meta = 2000
    actual = 0
    porcentaje = 0
    meta_semanal = 14000
    actual_semanal = 0
    porcentaje_semanal = 0

    if request.method == "POST":
        try:
            meta = float(request.form.get("meta", meta))
            actual = float(request.form.get("actual", actual))
            porcentaje = min((actual / meta) * 100, 100) if meta > 0 else 0

            actual_semanal = float(request.form.get("actual_semanal", actual * 3))
            porcentaje_semanal = min((actual_semanal / meta_semanal) * 100, 100)
        except ValueError:
            pass

    return render_template(
        "horarioC.html",
        meta=int(meta),
        actual=int(actual),
        porcentaje=porcentaje,
        meta_semanal=int(meta_semanal),
        actual_semanal=int(actual_semanal),
        porcentaje_semanal=porcentaje_semanal
    )


@app.route("/recetas", methods=["GET", "POST"])
def recetas():
    resultados = None
    recomendaciones = None

    if request.method == "POST":
        consulta = request.form.get("buscar", "")


        resultados = buscar_recetas_api(consulta)

        if len(consulta) >= 3:
            recomendaciones = buscar_recetas_api(consulta[:3])

    return render_template(
        "recetas.html",
        resultados=resultados,
        recomendaciones=recomendaciones
    )

    
@app.route("/detalle/<int:fdc_id>")
def detalle(fdc_id):
    return render_template("detalle.html", id=fdc_id)



@app.route("/acerca")
def acerca():
    return render_template("acerca.html")


@app.route("/ejercicio", methods=["GET", "POST"])
def ejercicio():
    porcentaje = 0
    if request.method == "POST":
        completado = int(request.form.get("completado", 0))
        total = int(request.form.get("total", 1))
        porcentaje = min(100, (completado / total) * 100)
    return render_template("ejercicio.html", porcentaje=porcentaje)


@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if request.method == "POST":
        
        nombre = request.form.get("nombre", "")
        apellido = request.form.get("apellido", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        genero = request.form.get("genero", "")
        experiencia = request.form.get("experiencia", "")
        objetivos = request.form.get("objetivos", "")
        alergias = request.form.get("alergias", "")
        intolerancias = request.form.get("intolerancias", "")
        dietas = request.form.get("dietas", "")
        no_gustan = request.form.get("no_gustan", "")

        session["usuario"] = email
        
        return render_template(
            "perfil.html",
            nombre=nombre,
            apellido=apellido,
            email=email,
            password=password,
            genero=genero,
            experiencia=experiencia,
            objetivos=objetivos,
            alergias=alergias,
            intolerancias=intolerancias,
            dietas=dietas,
            no_gustan=no_gustan
        )
    else:
        return render_template(
            "perfil.html",
            nombre="",
            apellido="",
            email="",
            password="",
            genero="",
            experiencia="",
            objetivos="",
            alergias="",
            intolerancias="",
            dietas="",
            no_gustan=""
        )


@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    resultado = None

    if request.method == 'POST':
        genero = request.form.get('genero')
        peso = float(request.form.get('peso'))
        altura = float(request.form.get('altura'))  
        edad = int(request.form.get('edad'))

        imc_valor = round(peso / (altura * altura), 1)

        if imc_valor < 18:
            clasificacion = "Bajo peso"
            riesgo = "Riesgo bajo pero requiere vigilancia nutricional."
        elif imc_valor < 25:
            clasificacion = "Peso normal"
            riesgo = "Riesgo bajo, mantener hábitos saludables."
        elif imc_valor < 30:
            clasificacion = "Sobrepeso"
            riesgo = "Aumento del riesgo de enfermedades."
        elif imc_valor < 35:
            clasificacion = "Obesidad Grado I"
            riesgo = "Riesgo moderado, recomendable atención médica."
        elif imc_valor < 40:
            clasificacion = "Obesidad Grado II"
            riesgo = "Riesgo alto, seguimiento profesional necesario."
        else:
            clasificacion = "Obesidad Grado III"
            riesgo = "Riesgo muy alto, intervención médica inmediata."

        resultado = {
            "genero": genero,
            "edad": edad,
            "imc": imc_valor,
            "clasificacion": clasificacion,
            "riesgo": riesgo
        }

    return render_template("calculadora.html", resultado=resultado)



@app.route("/info")
def info():
    return render_template("info.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("lobby"))


if __name__ == "__main__":
    app.run(debug=True)
