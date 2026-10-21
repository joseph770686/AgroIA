/*=========================================================
AGROVISION AI
FRONTEND REAL

========================================================= */





/* =========================================================

   ELEMENTOS

========================================================= */



const imageInput =

    document.getElementById("imageInput");



const selectImageBtn =

    document.getElementById("selectImageBtn");



const previewImage =

    document.getElementById("previewImage");



const previewEmpty =

    document.getElementById("previewEmpty");



const fileName =

    document.getElementById("fileName");



const analyzeBtn =

    document.getElementById("analyzeBtn");



const loading =

    document.getElementById("loading");



const resultCard =

    document.getElementById("resultCard");



const resultCrop =

    document.getElementById("resultCrop");



const resultState =

    document.getElementById("resultState");



const resultType =

    document.getElementById("resultType");



const resultConfidence =

    document.getElementById("resultConfidence");



const confidenceBar =

    document.getElementById("confidenceBar");



const probabilityList =

    document.getElementById("probabilityList");



const breadcrumb =

    document.getElementById("breadcrumb");





/* =========================================================

   NAVEGACIÓN

========================================================= */



const navItems =

    document.querySelectorAll(".nav-item[data-section]");



const sections =

    document.querySelectorAll(".section");





function mostrarSeccion(sectionId) {



    sections.forEach(section => {



        section.classList.remove(

            "active-section"

        );



    });





    const section =

        document.getElementById(sectionId);





    if (section) {



        section.classList.add(

            "active-section"

        );



    }





    navItems.forEach(item => {



        item.classList.remove("active");



        if (

            item.dataset.section ===

            sectionId

        ) {



            item.classList.add("active");

           



        }



    });





    const nombres = {

    dashboard: "Panel de Control",

    analisis: "Cargar Análisis",

    historial: "Resultados Históricos",

    admin: "Administración"

};

document.getElementById("adminRefreshBtn")

    ?.addEventListener("click", async () => {

        await cargarEstadisticasAdmin();

        await cargarUsuariosAdmin();

    });



    breadcrumb.textContent =

        nombres[sectionId] ||

        "AgroVision AI";





    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

    if (sectionId === "historial") {

    cargarHistorial();

}



}





navItems.forEach(item => {



    item.addEventListener(

        "click",

        () => {



            mostrarSeccion(

                item.dataset.section

            );



        }

    );



});





/* Botones que llevan al análisis */



document

    .getElementById("heroAnalyzeBtn")

    ?.addEventListener(

        "click",

        () => mostrarSeccion("analisis")

    );





document

    .getElementById("chartAnalyzeBtn")

    ?.addEventListener(

        "click",

        () => mostrarSeccion("analisis")

    );





document

    .getElementById("adviceAnalyzeBtn")

    ?.addEventListener(

        "click",

        () => mostrarSeccion("analisis")

    );





document

    .getElementById("historyAnalyzeBtn")

    ?.addEventListener(

        "click",

        () => mostrarSeccion("analisis")

    );





document

    .querySelector(".view-all")

    ?.addEventListener(

        "click",

        () => mostrarSeccion("historial")

    );





/* =========================================================

   SELECCIONAR IMAGEN

========================================================= */



selectImageBtn.addEventListener(

    "click",

    () => {



        imageInput.click();



    }

);





/* =========================================================

   CAMBIO DE IMAGEN

========================================================= */



imageInput.addEventListener(

    "change",

    () => {



        const file =

            imageInput.files[0];





        if (!file) {



            return;



        }





        fileName.textContent =

            file.name; /* Mostrar preview */



        const reader =

            new FileReader();





        reader.onload =

            function(event) {



                previewImage.src =

                    event.target.result;



                previewImage.style.display =

                    "block";



                previewEmpty.style.display =

                    "none";



            };





        reader.readAsDataURL(file);





        /* Activar botón */



        analyzeBtn.disabled =

            false;





        /* Ocultar resultado anterior */



        resultCard.style.display =

            "none";



    }

);





/* =========================================================

   ANALIZAR

========================================================= */



analyzeBtn.addEventListener(

    "click",

    async () => {



        const file =

            imageInput.files[0];





        if (!file) {



            alert(

                "Primero selecciona una imagen."

            );



            return;



        }





        /* Estado */



        analyzeBtn.disabled =

            true;



        analyzeBtn.textContent =

            "Analizando...";



        loading.style.display =

            "flex";





        resultCard.style.display =

            "none";





        try {



            /* FormData */



            const formData =

                new FormData();





            formData.append(

                "file",

                file

            );





            /* Petición al backend */



            const token = sessionStorage.getItem("agrovision_token");



            const response = await fetch("/analizar", {

              method: "POST",

              headers: {

                  "Authorization": `Bearer ${token}`

                 },

                 body: formData

                 });





            const data =

                await response.json();





            /* Error del backend */



            if (!response.ok) {



                throw new Error(

                    data.detail ||

                    "No se pudo analizar la imagen."

                );



            }





            console.log(

                "Resultado IA:",

                data

            );





            /* Información */



            const info =

                data.informacion;





            /* Mostrar datos */



            resultCrop.textContent =

                info.cultivo || "-";





            resultState.textContent =

                info.estado || "-";





            resultType.textContent =

                info.tipo || "-";





            const confianza =

                Number(

                    data.confianza || 0

                );





            resultConfidence.textContent =

                confianza + "%";





            /* Barra */



            confidenceBar.style.width =

                confianza + "%";





            /* Probabilidades */



            mostrarProbabilidades(

                data.probabilidades

            );





            /* Mostrar tarjeta */



            resultCard.style.display =

                "block";

           // Actualizar historial, análisis recientes y estadísticas

            await cargarHistorial();



            /* Scroll */



            resultCard.scrollIntoView({

                behavior: "smooth",

                block: "start"

            });





        } catch (error) {



            console.error(

                "Error:",

                error

            );





            alert(

                "No se pudo analizar la imagen.\n\n" +

                error.message

            );



        } finally {



            analyzeBtn.disabled =

                false;



            analyzeBtn.textContent =

                "Analizar cultivo";



            loading.style.display =

                "none";



        }



    }

);/* =========================================================

   PROBABILIDADES

========================================================= */



function mostrarProbabilidades(

    probabilidades

) {



    probabilityList.innerHTML =

        "";





    if (

        !probabilidades ||

        Object.keys(probabilidades).length === 0

    ) {



        probabilityList.innerHTML =

            "<p>No hay probabilidades disponibles.</p>";



        return;



    }





    const ordenadas =

        Object.entries(probabilidades)

            .sort(

                (a, b) =>

                    Number(b[1]) -

                    Number(a[1])

            );





    ordenadas.forEach(

        ([clase, valor]) => {



            const percentage =

                Number(valor);





            const row =

                document.createElement(

                    "div"

                );





            row.className =

                "probability-row";





            row.innerHTML = `



                <div class="probability-top">



                    <span>

                        ${formatearClase(clase)}

                    </span>



                    <strong>

                        ${percentage}%

                    </strong>



                </div>



                <div class="probability-track">



                    <div

                        class="probability-fill"

                        style="width: ${percentage}%"

                    ></div>



                </div>



            `;





            probabilityList.appendChild(

                row

            );



        }

    );



}





/* =========================================================

   FORMATEAR CLASE

========================================================= */



function formatearClase(

    clase

) {



    const nombres = {



        arroz_enfermo:

            "Arroz enfermo",



        arroz_sano:

            "Arroz sano",



        frijol_enfermo:

            "Frijol enfermo",



        frijol_sano:

            "Frijol sano",



        maiz_enfermo:

            "Maíz enfermo",



        maiz_plaga:

            "Maíz con plaga",



        maiz_sano:

            "Maíz sano"



    };





    return (

        nombres[clase] ||

        clase

    );



}





/* =========================================================

   HISTORIAL, ANÁLISIS RECIENTES Y ESTADÍSTICAS

========================================================= */



async function cargarHistorial() {

    const tokenActual = sessionStorage.getItem("agrovision_token");



    if (!tokenActual) {

        return;

    }



    try {

        const response = await fetch("/historial", {

            method: "GET",

            headers: {

                "Authorization": `Bearer ${tokenActual}`

            }

        });



        if (!response.ok) {

            throw new Error("No se pudo cargar el historial.");

        }



        const data = await response.json();



        if (!data.exito || !Array.isArray(data.historial)) {

            throw new Error("La respuesta del historial no es válida.");

        }



        renderizarHistorial(data.historial);

        actualizarEstadisticas(data.historial);

        renderizarRecientes(data.historial);



    } catch (error) {

        console.error("Error cargando historial:", error);

    }

}





/* Mostrar todos los análisis guardados */



function renderizarHistorial(historial) {

    const seccion = document.getElementById("historial");



    if (!seccion) {

        return;

    }



    // Ocultar el mensaje estático que decía que no había historial.

    const mensajeVacio = seccion.querySelector(".history-empty");



    if (mensajeVacio) {

        mensajeVacio.style.display = "none";

    }



    let contenedor = document.getElementById("historyResults");



    if (!contenedor) {

        contenedor = document.createElement("div");

        contenedor.id = "historyResults";

        contenedor.className = "history-results";

        seccion.appendChild(contenedor);

    }



    contenedor.replaceChildren();



    if (historial.length === 0) {

        const mensaje = document.createElement("p");

        mensaje.textContent = "Todavía no tienes análisis guardados.";

        contenedor.appendChild(mensaje);

        return;

    }



    historial.forEach(registro => {

        const tarjeta = document.createElement("article");

        tarjeta.className = "panel history-card";



        const titulo = document.createElement("h3");

        titulo.textContent = registro.cultivo || "Cultivo";



        const resultado = document.createElement("p");

        resultado.textContent =

            "Resultado: " + formatearClase(registro.resultado || "Sin resultado");



        const estado = document.createElement("p");

        estado.textContent = "Estado: " + (registro.estado || "No disponible");



        const confianza = document.createElement("p");

        confianza.textContent =

            "Confianza: " + formatearConfianza(registro.confianza);



        const enfermedad = document.createElement("p");

        enfermedad.textContent =

            "Diagnóstico: " + (registro.enfermedad || "No disponible");



        const recomendacion = document.createElement("p");

        recomendacion.textContent =

            "Recomendación: " + (registro.recomendacion || "No disponible");



        const fecha = document.createElement("small");

        fecha.textContent = "Fecha: " + formatearFecha(registro.fecha_analisis);



        tarjeta.append(

            titulo,

            resultado,

            estado,

            confianza,

            enfermedad,

            recomendacion,

            fecha

        );



        contenedor.appendChild(tarjeta);

    });

}



/* Actualizar estadísticas del panel */



function actualizarEstadisticas(historial) {

    const total = document.getElementById("totalAnalyses");

    const cultivos = document.getElementById("cropCount");

    const alertas = document.getElementById("alertCount");



    const cultivosUnicos = new Set(

        historial

            .map(registro => registro.cultivo)

            .filter(Boolean)

            .map(cultivo => cultivo.toLowerCase())

    );



    // Se considera alerta cualquier resultado que no sea sano.

    const totalAlertas = historial.filter(registro => {

        const estado = String(registro.estado || "").toLowerCase();

        const resultado = String(registro.resultado || "").toLowerCase();



        return (

            estado.includes("enfermo") ||

            estado.includes("plaga") ||

            resultado.includes("enfermo") ||

            resultado.includes("plaga")

        );

    }).length;



    if (total) {

        total.textContent = historial.length;

    }



    if (cultivos) {

        cultivos.textContent = cultivosUnicos.size;

    }



    if (alertas) {

        alertas.textContent = totalAlertas;

    }

}





/* Mostrar los análisis más recientes en el panel */



function renderizarRecientes(historial) {

    const lista = document.getElementById("recentAnalyses");



    if (!lista) {

        return;

    }



    lista.replaceChildren();



    if (historial.length === 0) {

        const mensaje = document.createElement("p");

        mensaje.textContent = "Todavía no tienes análisis recientes.";

        lista.appendChild(mensaje);

        return;

    }



    historial.slice(0, 5).forEach(registro => {

        const elemento = document.createElement("div");

        elemento.className = "recent-analysis-item";



        const titulo = document.createElement("strong");

        titulo.textContent = registro.cultivo || "Cultivo";



        const resultado = document.createElement("p");

        resultado.textContent = formatearClase(registro.resultado || "Sin resultado");



        const fecha = document.createElement("small");

        fecha.textContent = formatearFecha(registro.fecha_analisis);



        elemento.append(titulo, resultado, fecha);

        lista.appendChild(elemento);

    });

}





/* Formatear confianza y fecha */



function formatearConfianza(valor) {

    const numero = Number(valor);



    if (!Number.isFinite(numero)) {

        return "No disponible";

    }



    return numero + "%";

}



function formatearFecha(valor) {

    if (!valor) {

        return "Fecha no disponible";

    }



    const fecha = new Date(valor);



    if (Number.isNaN(fecha.getTime())) {

        return valor;

    }



    return fecha.toLocaleString("es-SV", {

        dateStyle: "medium",

        timeStyle: "short"

    });

}



/* =========================================================

   ESTADO INICIAL

========================================================= */



mostrarSeccion(

    "dashboard"

);



/* ==========================================

   SESIÓN Y PERFIL DEL USUARIO

========================================== */



const token = sessionStorage.getItem("agrovision_token");

const usuarioGuardado = sessionStorage.getItem("agrovision_usuario");

console.log("Token detectado:", !!token);

console.log("Usuario detectado:", !!usuarioGuardado);



if (!token || !usuarioGuardado) {

    window.location.replace("/login");

} else {

    try {

        const usuario = JSON.parse(usuarioGuardado);



        document.getElementById("profileName").textContent =

            usuario.nombre || "Usuario";



        document.getElementById("profileRole").textContent =

            usuario.rol === "administrador"

                ? "ADMINISTRADOR"

                : "USUARIO";



        document.getElementById("profileAvatar").textContent =

            (usuario.nombre || "U").charAt(0).toUpperCase();



    } catch (error) {

        sessionStorage.removeItem("agrovision_token");

        sessionStorage.removeItem("agrovision_usuario");

        window.location.replace("/login");

    }

}

// Cargar los datos guardados al iniciar el panel

if (token && usuarioGuardado) {

    cargarHistorial();

}

/* =========================================================

   MÓDULO DE ADMINISTRADOR

========================================================= */



async function cargarEstadisticasAdmin() {

    const tokenAdmin = sessionStorage.getItem("agrovision_token");



    if (!tokenAdmin) return;



    try {

        const respuesta = await fetch("/admin/estadisticas", {

            headers: {

                "Authorization": `Bearer ${tokenAdmin}`

            }

        });



        const datos = await respuesta.json();



        if (!respuesta.ok) {

            throw new Error(datos.detail || "No se pudieron cargar las estadísticas.");

        }



        const elementos = {

            adminTotalUsuarios: datos.total_usuarios,

            adminTotalAnalisis: datos.total_analisis,

            adminCultivosAnalizados: datos.cultivos_analizados,

            adminTotalAlertas: datos.total_alertas

        };



        Object.entries(elementos).forEach(([id, valor]) => {

            const elemento = document.getElementById(id);



            if (elemento) {

                elemento.textContent = valor ?? 0;

            }

        });



    } catch (error) {

        console.error("Error en estadísticas administrativas:", error);

    }

}





async function cargarUsuariosAdmin() {

    const tokenAdmin = sessionStorage.getItem("agrovision_token");



    if (!tokenAdmin) return;



    const tabla = document.getElementById("adminUsuarios");



    if (!tabla) return;



    try {

        const respuesta = await fetch("/admin/usuarios", {

            headers: {

                "Authorization": `Bearer ${tokenAdmin}`

            }

        });



        const datos = await respuesta.json();



        if (!respuesta.ok) {

            throw new Error(datos.detail || "No se pudieron cargar los usuarios.");

        }

console.log(

    "RESPUESTA COMPLETA DE USUARIOS:",

    JSON.stringify(datos, null, 2)

);

        tabla.replaceChildren();



 

const usuarios = datos.usuarios;



if (!datos.exito || !Array.isArray(usuarios)) {

    throw new Error("La respuesta del backend no contiene una lista válida de usuarios.");

}



if (usuarios.length === 0) {

    const fila = document.createElement("tr");

    const celda = document.createElement("td");



    celda.colSpan = 4;

    celda.textContent = "No hay usuarios registrados.";

    fila.appendChild(celda);

    tabla.appendChild(fila);

    return;

}



        usuarios.forEach(usuario => {

            const fila = document.createElement("tr");



            [

                usuario.id_usuario,

                usuario.nombre,

                usuario.correo,

                usuario.rol

            ].forEach(valor => {

                const celda = document.createElement("td");

                celda.textContent = valor ?? "";

                fila.appendChild(celda);

            });



            tabla.appendChild(fila);

        });



    } catch (error) {

        console.error("Error cargando usuarios:", error);



        tabla.replaceChildren();



        const fila = document.createElement("tr");

        const celda = document.createElement("td");



        celda.colSpan = 4;

        celda.textContent = error.message;

        fila.appendChild(celda);

        tabla.appendChild(fila);

    }

}





/* Mostrar el módulo solo al administrador */



function configurarModuloAdmin() {

    let usuario;



    try {

        usuario = JSON.parse(

            sessionStorage.getItem("agrovision_usuario") || "null"

        );

    } catch {

        usuario = null;

    }



    const esAdmin = usuario?.rol === "administrador";



    document.querySelectorAll("[data-admin-only]").forEach(elemento => {

        elemento.style.display = esAdmin ? "" : "none";

    });



    if (esAdmin) {

        cargarEstadisticasAdmin();

        cargarUsuariosAdmin();

    }

}



configurarModuloAdmin();

