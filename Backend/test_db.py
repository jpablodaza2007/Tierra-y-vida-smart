import psycopg2

print("Probando conexión a la base de datos de Tierra Y Vida Smart...")

try:
    conexion = psycopg2.connect(
        dbname="tierra_y_vida_smart",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )
    
    print("✅ ¡Éxito! Conexión establecida correctamente con PostgreSQL.")
    
    conexion.close()

except Exception as error:
    print("❌ Hubo un error al conectar. El mensaje real de PostgreSQL es:")
    print(repr(error))