from cmath import sqrt
from flask import Flask, request, render_template, jsonify
import main

app = Flask(__name__)

@app.route('/getdata', methods= ['GET'])
def stuff():
    mass = main.readLS()
    
    tx=main.MPU_getValue('wX')
    ty=main.MPU_getValue('wY')
    ax=main.MPU_getValue('aX')
    ay=main.MPU_getValue('aY')
    az=main.MPU_getValue('aZ')
    return jsonify(mass=mass,tx=tx,ty=ty,ax=ax,ay=ay,az=az)

@app.route('/getdataB', methods= ['GET'])
def stuffB():
    speed = 0 #fastest speed
    tx=main.MPU_getValue('wX')
    ty=main.MPU_getValue('wY')
    ts=sqrt(tx^2 + ty^2)

    ax=main.MPU_getValue('aX')
    ay=main.MPU_getValue('aY')
    aS=sqrt(ax^2 + ay^2)

    return jsonify(speed=speed,tx=tx,ty=ty,ts=ts,ax=ax,ay=ay,aS=aS)

@app.route('/getdataC', methods= ['GET'])
def stuffC():
    mass = main.readLS()
    foamLevel = 0 #replace with foam level function
    dataLabels = ["a","b","c"] #replace with list of timestamps
    dataValues = [1,2,3] #replace with list of color values
    return jsonify(m=mass,fl=foamLevel,l=dataLabels,v=dataValues)

@app.route('/partA', methods=["GET","POST"])
def partA():
    if request.method == "POST":
        btn = request.form['btn']
        if btn == "Tare":
            main.tareLS()
        if btn == "Calibrate LC":
            main.calibrateLS(request.form['amount'])
        if btn == "Go to angle":
            main.setAngle(request.form['targetA'])
        if btn == "Calibrate IMU":
            main.MPU_calibrate()
        if btn == "Capture Image":
            main.takePic()
    return render_template('partA.html')

@app.route('/partB', methods=["GET","POST"])
def partB():
    if request.method == "POST":
        btn = request.form['btn']
        if btn == "Calibrate":
            pass #calibration function goes here
    return render_template('partB.html')

@app.route('/partC', methods=["GET","POST"])
def partC():
    if request.method == "POST":
        btn = request.form['btn']
        if btn == "Calibrate Load Cell":
            main.calibrateLS(request.form['amount'])
        if btn == "Calibrate IMU":
            main.MPU_calibrate()
        if btn == "Program Start":
            pass #function to start program here
    return render_template('partC.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
