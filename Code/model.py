from flask import Flask, render_template
import psycopg2
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd  # Import pandas

app = Flask(__name__)

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname='patient db',
    user='postgres',
    password='Bhuvanesh@172629',
    host='127.0.0.1',
    port='5432'
)

# Define a route to fetch data and generate pie charts
@app.route('/blood', methods=['GET'])
def get_data():
    cursor = conn.cursor()
    cursor.execute('SELECT patients.*,preoperative.bloodgroup as BloodType,basic_metabolic_panel.status as bmp_status,cholesterol_test.status as chol_status,labtest.status as cbc_status,liver_function_test.status as lft_status,postoperative.complications,postoperative.readmission,postoperative.surgeonid,postoperative.surgerytype FROM patients JOIN basic_metabolic_panel ON patients.patientid =basic_metabolic_panel.patientid JOIN cholesterol_test ON patients.patientid =cholesterol_test.patientid JOIN labtest ON patients.patientid = labtest.patientid JOIN liver_function_test ON patients.patientid =liver_function_test.patientid JOIN postoperative ON patients.patientid =postoperative.patientid JOIN preoperative ON patients.patientid =preoperative.patientid')
    fetched_data = cursor.fetchall()
    cursor.close()

    # Process fetched data
    blood_groups = [row[6] for row in fetched_data]
    readmission_status = [row[12] for row in fetched_data]

    # Counting readmissions and no readmissions for each blood type
    blood_type_counts = {}
    for blood_group, status in zip(blood_groups, readmission_status):
        if blood_group not in blood_type_counts:
            blood_type_counts[blood_group] = {'Readmission': 0, 'No Readmission': 0}
        if status:
            blood_type_counts[blood_group]['Readmission'] += 1
        else:
            blood_type_counts[blood_group]['No Readmission'] += 1

    # Calculate percentages for each blood type
    blood_type_percentages = {}
    for blood_group, counts in blood_type_counts.items():
        total_counts = sum(counts.values())
        readmission_percentage = counts['Readmission'] / total_counts * 100
        blood_type_percentages[blood_group] = readmission_percentage

    # Find blood groups with readmission percentage above 60%
    high_readmission_groups = {blood_group: percentage for blood_group, percentage in blood_type_percentages.items() if percentage > 60}

    # Plotting
    charts = []
    for blood_group, percentages in blood_type_percentages.items():
        labels = ['Readmission', 'No Readmission']
        sizes = [percentages, 100 - percentages]  # Total size is 100%
        colors = ['#ff9999', '#66b3ff']
        explode = (0.1, 0)

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
        ax.set_title(f'Percentage of Readmission and No Readmission for Blood Type {blood_group}')
        ax.axis('equal')

        # Convert plot to base64 encoded image string
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        charts.append({'blood_group': blood_group, 'pie_chart': image_base64, 'readmission_percentage': percentages})

    return render_template('pie_chart.html', charts=charts, high_readmission_groups=high_readmission_groups)


@app.route('/bmp', methods=['GET'])
def get_bmp_data():
    cursor = conn.cursor()

    # Execute query
    cursor.execute('SELECT patients.*,preoperative.bloodgroup as BloodType,basic_metabolic_panel.status as bmp_status,cholesterol_test.status as chol_status,labtest.status as cbc_status,liver_function_test.status as lft_status,postoperative.complications,postoperative.readmission,postoperative.surgeonid,postoperative.surgerytype FROM patients JOIN basic_metabolic_panel ON patients.patientid =basic_metabolic_panel.patientid JOIN cholesterol_test ON patients.patientid =cholesterol_test.patientid JOIN labtest ON patients.patientid = labtest.patientid JOIN liver_function_test ON patients.patientid =liver_function_test.patientid JOIN postoperative ON patients.patientid =postoperative.patientid JOIN preoperative ON patients.patientid =preoperative.patientid')

    # Fetch data
    fetched_data = cursor.fetchall()
    cursor.close()

    # Convert data to DataFrame
    columns = ['Patient ID', 'Name', 'Age', 'Gender', 'Email', 'Insurance', 'Blood Type', 'BMP Status', 'Chol Status', 'CBC Status', 'LFT Status', 'Complications', 'Readmission', 'Surgery ID', 'Type']
    df = pd.DataFrame(fetched_data, columns=columns)

    # Grouping the DataFrame by 'BMP Status' and calculating the sum of readmissions
    bmp_readmission_counts = df.groupby('BMP Status')['Readmission'].sum()

    # Determine the BMP status with the highest readmission percentage
    highest_readmission_status = bmp_readmission_counts.idxmax()
    explode = [0.1 if status == highest_readmission_status else 0 for status in bmp_readmission_counts.index]

    # Plotting 3D Pie Chart with Depth Effect
    fig, ax = plt.subplots(figsize=(10, 7), subplot_kw=dict(aspect="equal"))

    wedges, texts, autotexts = ax.pie(bmp_readmission_counts, labels=bmp_readmission_counts.index, autopct='%1.1f%%', startangle=140, colors=['skyblue', 'lightgreen', 'lightcoral', 'lightyellow'], explode=explode, wedgeprops=dict(width=0.3, edgecolor='w'))

    ax.set_title('Distribution of Readmissions by BMP Status')

    # Adding shadow effect
    for w in wedges:
        w.set_zorder(1)
        w.set_edgecolor('w')

    for t in texts:
        t.set_zorder(2)

    for at in autotexts:
        at.set_zorder(3)
        if at.get_text().startswith(str(bmp_readmission_counts.max())):
            at.set_color('red')
            at.set_fontsize(14)
            at.set_fontweight('bold')
            at.set_animated(True)
            at.set_alpha(0.5)

    # Save plot to a buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    return render_template('bmp.html', bmp_pie_chart=image_base64, highest_readmission_status=highest_readmission_status)


@app.route('/surgery', methods=['GET'])
def get_surgery_data():
    cursor = conn.cursor()

    # Execute query
    cursor.execute('SELECT patients.*,preoperative.bloodgroup as BloodType,basic_metabolic_panel.status as bmp_status,cholesterol_test.status as chol_status,labtest.status as cbc_status,liver_function_test.status as lft_status,postoperative.complications,postoperative.readmission,postoperative.surgeonid,postoperative.surgerytype FROM patients JOIN basic_metabolic_panel ON patients.patientid =basic_metabolic_panel.patientid JOIN cholesterol_test ON patients.patientid =cholesterol_test.patientid JOIN labtest ON patients.patientid = labtest.patientid JOIN liver_function_test ON patients.patientid =liver_function_test.patientid JOIN postoperative ON patients.patientid =postoperative.patientid JOIN preoperative ON patients.patientid =preoperative.patientid')

    # Fetch data
    fetched_data = cursor.fetchall()
    cursor.close()

    # Convert data to DataFrame
    columns = ['Patient ID', 'Name', 'Age', 'Gender', 'Email', 'Insurance', 'Blood Type', 'BMP Status', 'Chol Status', 'CBC Status', 'LFT Status', 'Complications', 'Readmission', 'Surgery ID', 'Type']
    df = pd.DataFrame(fetched_data, columns=columns)

    # Grouping the DataFrame by 'Type' and calculating the sum of readmissions
    surgery_readmission_counts = df.groupby('Type')['Readmission'].sum()

    # Determine the surgery type with the highest readmission count
    highest_readmission_type = surgery_readmission_counts.idxmax()
    explode = [0.1 if surgery_type == highest_readmission_type else 0 for surgery_type in surgery_readmission_counts.index]

    # Plotting Pie Chart with Depth Effect
    fig, ax = plt.subplots(figsize=(10, 7), subplot_kw=dict(aspect="equal"))

    wedges, texts, autotexts = ax.pie(surgery_readmission_counts, labels=surgery_readmission_counts.index, autopct='%1.1f%%', startangle=140, colors=['skyblue', 'lightgreen', 'lightcoral', 'lightyellow'], explode=explode, wedgeprops=dict(width=0.3, edgecolor='w'))

    ax.set_title('Distribution of Readmissions by Surgery Type')

    # Adding shadow effect
    for w in wedges:
        w.set_zorder(1)
        w.set_edgecolor('w')

    for t in texts:
        t.set_zorder(2)

    for at in autotexts:
        at.set_zorder(3)
        if at.get_text().startswith(str(surgery_readmission_counts.max())):
            at.set_color('red')
            at.set_fontsize(14)
            at.set_fontweight('bold')
            at.set_animated(True)
            at.set_alpha(0.5)

    # Save plot to a buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    return render_template('surgery.html', surgery_pie_chart=image_base64, highest_readmission_type=highest_readmission_type)
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
