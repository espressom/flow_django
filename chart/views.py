# import numpy as np
# from PIL import Image
# from django.shortcuts import render
# # import pandas as pd
# # import numpy as np
# # import cx_Oracle as ora
# # from django.views.decorators.csrf import csrf_protect
# # from tensorflow.keras.models import load_model
# from django.views.decorators.csrf import csrf_exempt
#
# from tensorflow.python.keras.models import load_model, model_from_json
# import tensorflow as tf
# from tensorflow.python.keras.preprocessing.image import  load_img
# import matplotlib.pyplot as plt
#
# UPLOAD_DIR = "/home/myubuntu/PycharmProjects/flow/chart/static/images/"
#
# def main2(request):
#     return render(request,'chart/upform2.html')
#
# @csrf_exempt
# def upload_success2(request):
#     print(' >>>>>> upload_success2 >>>>>> ')
#     # 첨부파일이 있는 경우
#     if "file1" in request.FILES:
#         # <input type="file" name="file1"
#         file = request.FILES["file1"]
#         file_name = file._name  # 첨부파일 이름
#         print('file_name ::::' , file_name)
#         # 파일 오픈(wb:write binary)
#         print('path :::: ' + "%s%s" % (UPLOAD_DIR, file_name))
#         fp = open("%s%s" % (UPLOAD_DIR, file_name), "wb")
#         # 파일을 1바이트씩 조금씩 읽어서 저장
#         for chunk in file.chunks():
#             fp.write(chunk)
#         # 파일 닫기
#         fp.close()
#
#         json_file = open("/home/myubuntu/PycharmProjects/flow/chart/static/model/catdog_model.json", "r")
#         loaded_model_json = json_file.read()
#         json_file.close()
#         # json model load
#         loaded_model = model_from_json(loaded_model_json)
#         # weight model
#         loaded_model.load_weights("/home/myubuntu/PycharmProjects/flow/chart/static/model/catdog_model.h5")
#
#         # compile
#         loaded_model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
#         image = Image.open("%s%s" % (UPLOAD_DIR, file_name))
#         width = 64
#         height = 64
#         color = 3  # 색의 수
#         image = image.resize((width, height))
#
#         # normal
#         image = np.array(image)
#         print(image.shape)  # (150, 150, 3)
#         x_test = [image]
#         x_test = np.array(x_test)
#         x_test = x_test / 255
#
#         y_predict = loaded_model.predict(x_test)
#         print(y_predict)  # [[0.9948258]]
#         print(y_predict.flatten())
#         print(y_predict.flatten()[0])
#         print("------------------------------------------")
#         category = ""
#         if y_predict >= 0.5:
#             category = "cat"
#             print("cat", y_predict)
#         else:
#             category = "dog"
#             print("dog", y_predict)
#         print("------------------------------------------")
#     else:  # 첨부파일이 없는 경우
#         file_name = "-"
#
#     return render(request, 'chart/success2.html', {'category': category})


# def myform(request):
#     return render(request, "surveyform.html")
#
# @csrf_protect
# def gores(request):
#     # 파라미터 저장
#     gender = (int)(request.POST['gender'])
#     age = (int)(request.POST['age'])
#     pay = (int)(request.POST['pay'])
#     kind = (int)(request.POST['kind'])
#     season = (int)(request.POST['season'])
#     hobby = (int)(request.POST['hobby'])
#     term = (int)(request.POST['term'])
#
#     # 리스트로 저장
#     answer = []
#     answer.append(gender)
#     answer.append(age)
#     answer.append(pay)
#     answer.append(kind)
#     # answer.append(season)
#     # answer.append(hobby)
#     # answer.append(term)
#     print(answer)
#     answerlist = np.array(answer)
#     frame = pd.DataFrame([answerlist], columns=['Gender', 'Age', 'EstimatedSalary', 'Tstyle'])
#     print(frame.head())
#
#     # load_model, min, max
#     model = load_model('/home/myubuntu/PycharmProjects/flow/chart/static/model_test.h5')
#     df_min = pd.read_csv('/home/myubuntu/PycharmProjects/flow/chart/static/df_min.csv')
#     df_max = pd.read_csv('/home/myubuntu/PycharmProjects/flow/chart/static/df_max.csv')
#     dfMin = df_min['0']
#     dfMax = df_max['0']
#
#     # 인덱스 작업하기
#     dfMin.index = ['Gender', 'Age', 'EstimatedSalary', 'Tstyle', 'Purchased']
#     dfMax.index = ['Gender', 'Age', 'EstimatedSalary', 'Tstyle', 'Purchased']
#
#     # 임의의 값 설정 해서 테스트
#     # Xdata = np.array([[1, 46, 4100, 3]])
#     # test_Df = pd.DataFrame(Xdata, columns=['Gender', 'Age',
#     #                                        'EstimatedSalary',
#     #                                        'Tstyle'])
#     # test = (test_Df - dfMin) / (dfMax - dfMin)
#     # test1 = test[['Gender', 'Age', 'EstimatedSalary', 'Tstyle']]
#     # pp = model.predict(test1)
#     # print('Predict ::::', np.argmax(pp))
#
#     # 실제 값 설정 해서 테스트
#     pp = model.predict(frame)
#     print('Predict ::::', np.argmax(pp))
#
#     return render(request, "surveyres.html", {'predictVal' : np.argmax(pp)})