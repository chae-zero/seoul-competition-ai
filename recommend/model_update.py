#!/usr/bin/env python
# coding: utf-8

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import os
from joblib import dump
from konlpy.tag import Mecab
from datetime import datetime as dt

import numpy as np
import pandas as pd

import re
import requests
import json

import warnings
warnings.filterwarnings("ignore")

# 모델 및 df 존재 확인 
def check_model_data() :
    '''
    - 모델 및 data가 존재하는지 확인 
    - 존재하지 않는 경우 모델 및 data 생성 
    '''
    # 모델 저장 경로 : '/data/tfidf.pkl'
    # 데이터 저장 경로 : '/data/data.pkl'
    model = '/data/tfidf.pkl'
    data  = '/data/data.pkl'
    
    # 모델과 데이터 존재 확인 
    if os.path.isfile(model) and os.path.isfile(data):
        # print("파일 있음")
        return True
    else :
        print("파일 없음")
        # 최초 모델 및 데이터 생성 코드 실행 추가 
        init_model_data()


# 최초 모델 및 df 생성 
def init_model_data() :
    '''
    - 전체 데이터에 대한 모델 생성 및 데이터 프레임 저장 
    - 교육 정보 backend에 전체 데이터 요청하는 부분 맞추기 
    
    
    return 없음 : model, dataframe 두 개의파일 pkl로 저장 
    '''
    # 교육 정보 backend에 현재 존재하는 전체 데이터 요청 코드 작성 
    
    # 요청 및 json 데이터 변환
#     response = requests.get(DATA_URL)
#     response_data = response.content.decode()
#     json_data = json.loads(response_data)
#     data = pd.json_normalize(json_data[list( json_data.keys() )[0]]['row'])
    
    # 받아온 데이터에 대한 컬럼명, 전처리 등 수행 
    data = date_preprocessing(data)
    data = data_preprocessing(data)

    # 저장 
    save_model(data)
    save_dataframe(data)    


def concat_data(data1, data2 ) :
    '''
    - 초기 모델 생성을 위하여 공공데이터를 json 형태로 받아와 데이터프레임으로 생성.
    - 이후 백엔드에서 데이터를 받아오는 과정으로 변경시 사용하지 않음.
    - 초기에 사용하는 데이터가 2개이므로 병합하는 과정이 필요했음.

    data1 : DataFrame
    data2 : DataFrame

    return : pd.DataFrame

    '''
    # 컬럼명 통일 시키는 과정
    data1.columns = ['교육넘버', '교육명', '교육신청시작일', '교육신청종료일', '교육시작일', '교육종료일', "수업시간", '수강정원', '교육상태', '교육비용', '강좌상세화면']
    data2.columns = ["교육넘버", "교육명", "교육시작일", "교육종료일", "교육신청시작일", "교육신청종료일", "수강정원", "교육비용", "교육상태", "강좌상세화면"]

    # 컬럼명 순서 통일
    col_sort = ['교육넘버', '교육명', '교육신청시작일', '교육신청종료일', '교육시작일', '교육종료일',  '수강정원','교육상태', '교육비용', '강좌상세화면']

    data_1 = data1[ col_sort ]
    data_2 = data2[ col_sort ]
    # 이후 concat 진행
    data = pd.concat([data_1, data_2])

    return data


def date_preprocessing(dataframe) :
    '''
    - 두 개의 데이터 프레임이 날짜 표현을 서로 다른 방식으로 표현함
    - 신청 가능한 교육을 날짜 기준으로 선정할 예정이므로 datetime을 사용하기 위해 날짜 형식 변경
    - 이후 백엔드에서 데이터를 받아오는 경우 수정되거나 사용되지 않을 수 있음.

    dataframe  : dataframe

    return : dataframe

    '''
    ## 날짜 정보 datetime

    # 표현 형식 변경
    dataframe["교육신청시작일"] = dataframe["교육신청시작일"].apply(lambda x : re.sub(r"\.", r"-", x) )
    dataframe["교육신청종료일"] = dataframe["교육신청종료일"].apply(lambda x : re.sub(r"\.", r"-", x) )
    dataframe["교육시작일"] = dataframe["교육시작일"].apply(lambda x : re.sub(r"\.", r"-", x) )
    dataframe["교육종료일"] = dataframe["교육종료일"].apply(lambda x : re.sub(r"\.", r"-", x) )

    # int, datetime 형태 변경
    date_trans_col = ["교육신청시작일","교육신청종료일","교육시작일","교육종료일"]

    for col in date_trans_col :
        dataframe[col] = pd.to_datetime( dataframe[col] )

    return dataframe


# 불용어 처리
def clean_sentence(sentence) :
    '''
    - 데이터 분석 이후 문장에서 의미가 없을 것으로 판단되는 단어 불용어로 판단하여 처리

    sentence : Series

    return : Series

    '''

    # 날짜, 기수, 차수 제거
    sentence = re.sub(r"[0-9]+년", r" ", sentence)
    sentence = re.sub(r"[0-9]+차", r" ", sentence)
    sentence = re.sub(r"[0-9]+기", r" ", sentence)
    sentence = re.sub(r"[0-9]+월", r" ", sentence)
    sentence = re.sub(r"[0-9]+일", r" ", sentence)
    sentence = re.sub(r"[0-9]{1,2}.[0-9]{1,2}", r" ", sentence)

    # (주) , (요일)
    sentence = re.sub(r"\(+[가-힣]+\)", r" ", sentence)
    sentence = re.sub(r"[가-힣]째주", r" ", sentence)
    sentence = re.sub(r"[가-힣]{1}요일", r" ", sentence)

    # 마감 키워드 필요 없음
    sentence = re.sub(r"마감", r" ", sentence)

    # 50이라는 숫자 필요 없음
    sentence = re.sub(r"50", r" ", sentence)
    # 자격증 n급 필요 없을듯
    sentence = re.sub(r"[0-9]+급", r" ", sentence)
    # n단계도 필요 없을듯
    sentence = re.sub(r"[0-9]+단계", r" ", sentence)
    sentence = re.sub(r"[^0-9가-힣a-zA-Z]", r" ", sentence)

    return sentence


def tokenize(original_sent):
    '''
    - Mecab 형태소 분석기를 사용하여 문장를 "명사" 단위로 분류
    - 현 데이터는 문장의 의미보다는 사용되는 핵심 단어가 중요할 것으로 판단하여 결정

    sentence : Series

    return : Series

    '''

    tokenizer = Mecab()

    # tokenizer를 이용하여 original_sent를 토큰화하여 tokenized_sent에 저장하고, 이를 반환합니다.
    sentence = original_sent.replace('\n', '').strip()

    # tokenizer.nouns(sentence) -> 명사만 추출
    tokens = tokenizer.nouns(sentence)

    tokens = ' '.join(tokens)

    return tokens

def data_preprocessing(dataframe) :
    '''
    -  정의된 불용어 처리, 토크나이저를 데이터에 적용

    dataframe : dataframe

    return : dataframe

    '''
    # 교육명 불용어 처리하여 clean_sentence 컬럼으로 생성
    dataframe["clean_sentence"] = dataframe["교육명"].apply(lambda x : clean_sentence(x) )

    # 교육명 mecab 명사 토크나이징하여 mecab 컬럼으로 생성
    dataframe["mecab"] = dataframe["clean_sentence"].apply(lambda x : tokenize(x) )

    return dataframe

def save_model(data) :
    '''
    -  전체 데이터에 대한 tf-idf 모델 생성 후 저장

    data : dataframe

    '''
    path = os.path.join(os.getcwd(), 'data','/data/tfidf.pkl')
    tfidf_vector = TfidfVectorizer().fit( data["mecab"] )
    dump(tfidf_vector, path)


def save_dataframe(data) :
    path = os.path.join(os.getcwd(), 'data', '/data/data.pkl')
    data.to_pickle(path)


def model_update() :
    '''
    - 모델 업데이트
    - 일정 주기로 업데이트 시 실행할 수 있도록
    - .py 파일을 따로 생성하는 방법도 고려

    input_data : str
    data : dataframe
    vectorizer : TfidfVectorizer

    return : str

    '''

    API_KEY = "61484f6245666f7838344a79694e77"

    서울시50플러스포털교육정보 = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/FiftyPotalEduInfo/1/5/"
    서울시어르신취업지원센터교육정보 = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/tbViewProgram/1/5/"

    data_01 = get_dataframe(API_KEY, 서울시50플러스포털교육정보)
    data_02 = get_dataframe(API_KEY, 서울시어르신취업지원센터교육정보)
    total_data = concat_data(data_01, data_02)

    total_data = date_preprocessing(total_data)
    total_data = data_preprocessing(total_data)

    save_model(total_data)
    save_dataframe(total_data)

    print("모델 업데이트 완료")






