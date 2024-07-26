import streamlit as st
import pandas as pd
import plotly.express as px
import pickle
from local_components import card_container
import json

with open('data/total_students.pkl', 'rb') as file:
    total_students = pickle.load(file)

with open('map/TL_SCCO_CTPRVN.json') as response:
    korea_map = json.load(response)

# 대시보드 레이아웃 정의
st.set_page_config(
    page_title="한눈에 알아보는 학교 안전사고",
    layout="wide")

# 데이터 전처리
# pickle 라이브러리를 사용하여 데이터 불러오기
with open('data/edusafe.pkl', 'rb') as f:
    data = pickle.load(f)

# 페이지 출력 부분
first_col = st.columns((0.4, 0.3, 0.15, 0.15), gap='medium')

with first_col[0]:
    st.markdown('<h2 style="line-height: 150%;">🏫&nbsp;&nbsp;&nbsp;&nbsp;한눈에 알아보는 학교 안전사고</h2>', unsafe_allow_html=True)

with first_col[1]:
    st.write('연도를 선택하세요. (미 체크 시 전체 데이터 반영)')
    query_year = []
    query_year_text = ''
    first_inner_col = st.columns((1, 1, 1), gap='medium')

    with first_inner_col[0]:
        if st.checkbox('2019'):
            query_year += ['2019']
        if st.checkbox('2020'):
            query_year += ['2020']

    with first_inner_col[1]:
        if st.checkbox('2021'):
            query_year += ['2021']
        if st.checkbox('2022'):
            query_year += ['2022']

    with first_inner_col[2]:
        if st.checkbox('2023'):
            query_year += ['2023']

    for i in query_year:
        query_year_text += (i + '|')
    
    query_year_text = query_year_text[:-1]
    year_data = data[data.사고발생년도.str.contains(query_year_text)]
    total_students['Year'] = total_students['Year'].apply(lambda num: str(num))
    year_students = total_students[total_students.Year.str.contains(query_year_text)]

with first_col[2]:
    option = st.selectbox("학교급을 선택하세요.",
                          ('전체', '유치원', '초등학교', '중학교', '고등학교', '기타학교'))
    if option == '전체':
        handling_data = year_data
    elif option == '기타학교':
        handling_data = year_data[year_data.학교급.str.contains('특수학교|기타학교')]
    else:
        handling_data = year_data[year_data.학교급 == option]

    handling_data['사고장소'] = handling_data['사고장소'].replace('교외활동', '교외')

second_col = st.columns((1, 1, 1), gap='medium')

with second_col[0]:
    with card_container(key="card"):
        st.markdown('#### 시간대에 따른 사고 비율')

        # 시간 형식으로 변환
        handling_data['사고발생시각'] = pd.to_datetime(handling_data['사고발생시각'], format='%H:%M').dt.hour

        # 8시부터 20시까지 데이터 필터링
        hourly_filtered_df = handling_data[(handling_data['사고발생시각'] >= 8) & (handling_data['사고발생시각'] <= 20)]

        # 시간대별 사고 발생 수 계산
        hourly_counts = hourly_filtered_df['사고발생시각'].value_counts().sort_index()

        # 8시부터 20시까지 모든 시간대 포함
        all_hours = pd.Series(0, index=range(8, 21))
        hourly_counts = hourly_counts.add(all_hours, fill_value=0)
        hourly_counts.index.name = '사고발생시각'

        # 사고 발생 비율 계산
        hourly_percentage = ((hourly_counts / hourly_counts.sum()) * 100).to_frame(name="비율").reset_index()
        plot_percentage = hourly_percentage.copy()
        plot_percentage['사고발생시각'] = plot_percentage['사고발생시각'].apply(lambda x: str(x) + '시')

        bar_polar = px.bar_polar(plot_percentage, r='비율', theta='사고발생시각',
                                 color='비율', range_theta=[0, 180])
        bar_polar.update_traces(offset=0.05,
                                hovertemplate="비율: %{r:.2f}%",
                                selector=dict(type='barpolar'))
        bar_polar.update_layout(
            margin=dict(l=32, r=32, t=32, b=32),
            height=300
        )
        bar_polar.update_polars(
            angularaxis_ticks="outside",
            angularaxis_rotation=180,
            angularaxis_period=360/15,
            angularaxis_showline=False,
            #radialaxis_showgrid=False
        )
        st.plotly_chart(bar_polar, config = {'displayModeBar': False}, use_container_width=True)
        top3_hours = hourly_percentage.sort_values('비율', ascending=False).head(3)
        
        top3_hours['비율'] = top3_hours['비율'].apply(lambda x: round(x, 2))
        top3_hours['사고발생시각'] = top3_hours['사고발생시각'].apply(lambda x: str(x) + '시 ~ ' + str(x + 1) + '시')
        top3_hours = top3_hours.rename(columns={'비율': '비율(%)'})
        col1, col2, col3 = st.columns([0.1, 1, 0.1])
        with col2:
            st.dataframe(top3_hours.sort_values('비율(%)', ascending=False).head(3), hide_index=True,
                         column_config={'지역': st.column_config.Column(width='small'),
                                        '비율(%)': st.column_config.Column(width='medium')}, use_container_width=True)

    with card_container(key="card"):
        st.markdown('#### 사고 당사자 통계')

        gender = handling_data.groupby('사고자성별').count().구분
        rate = gender.남 / (gender.남 + gender.여) * 100
        st.markdown(f'<p style="margin: 0px 16px 12px 16px;">남: {round(rate, 2)}% / 여: {round(100-rate, 2)}%</p>', unsafe_allow_html=True)
        
        # 스타일 지정 및 남녀 비율 그래프 찍어내기
        st.markdown("""
        <style>
            .genderbar-child {
                width: """+f'{rate}'+"""%;
                align-self: stretch;
                position: relative;
                border-radius: 4px 0px 0px 4px;
                background-color: #b3defc;
                height: 8px;
                overflow: hidden;
                flex-shrink: 0;
            }
            .genderbar-wrapper {
                align-self: stretch;
                border-radius: 4px;
                background-color: #fcb3b3;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                justify-content: flex-start;
            }
            .genderbar-parent {
                width: calc(100% - 5.5vh);
                position: relative;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 0px 16px 16px 16px;
                box-sizing: border-box;
            }
        </style>
        <div class="genderbar-parent">
            <div class="genderbar-wrapper">
                <div class="genderbar-child">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if option in ['초등학교', '중학교', '고등학교', '기타학교']:
            if option == '초등학교':
                grade_index = 6
            elif option in ['중학교', '고등학교']:
                grade_index = 3
            else:
                grade_index = None
            grade = handling_data.groupby('사고자학년').count().구분.to_frame(name="건수").reset_index()[:grade_index]
            grade_bar = px.bar(grade, x='사고자학년', y='건수')
            grade_bar.update_traces(hovertemplate="학년: %{x}<br>건수: %{y:.f}건")
            grade_bar.update_xaxes(title_text='학년')
            grade_bar.update_layout(margin={"r":55,"t":0,"l":0,"b":0})
            st.plotly_chart(grade_bar, config = {'displayModeBar': False}, use_container_width=True)


with second_col[1]:
    with card_container(key="card"):
        st.markdown('#### 사고 장소')
        # 사고 장소 유형별 발생 건수 계산
        location_counts = handling_data['사고장소'].value_counts()

        # 비율 계산
        total_count = location_counts.sum()
        percentages = ((location_counts / total_count) * 100).to_frame('비율').reset_index()
        show_text = ''
        # for i in range(5):
        #     show_text += f'{percentages.loc[i].사고장소}: {round(percentages.loc[i].비율, 2)}% / '
        # show_text = show_text[:-3]
        
        treemap = px.treemap(data_frame=percentages, names='사고장소', parents=[show_text for _ in range(len(percentages))],
                             values='비율')
        treemap.update_traces(texttemplate="%{label}<br>%{value:.2f}%",
                              hovertemplate="사고장소: %{label}<br>비율: %{value:.2f}%",
                              textfont_size=16, textposition='middle center')
        treemap.update_layout(margin={"r":48,"t":0,"l":0,"b":0})
        st.plotly_chart(treemap, config = {'displayModeBar': False}, use_container_width=True)
        
    with card_container(key="card"):
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.markdown('#### 지역별 사고현황')
        with col2:
            if option != '유치원':
                scale = st.selectbox(label='확인할 지표를 선택하세요.', options=('학생 수', '사고 비율'))
            else:
                scale = '학생 수'
        
        locals = handling_data.groupby('지역').count().구분.to_frame(name="건수").reset_index()
        
        mapper = [
            ('경기', '경기도'),
            ('서울', '서울특별시'),
            ('충북', '충청북도'),
            ('인천', '인천광역시'),
            ('충남', '충청남도'),
            ('광주', '광주광역시'),
            ('부산', '부산광역시'),
            ('강원', '강원도'),
            ('전남', '전라남도'),
            ('대구', '대구광역시'),
            ('전북', '전라북도'),
            ('울산', '울산광역시'),
            ('제주', '제주특별자치도'),
            ('경북', '경상북도'),
            ('세종', '세종특별자치시'),
            ('경남', '경상남도'),
            ('대전', '대전광역시'),
        ]
        get_region = lambda gubun: [x[1] for x in mapper if x[0] == gubun][0]

        locals['EMD_KOR_NM'] = locals.지역.apply(get_region)

        if option == '전체':
            handling_students = year_students
        elif option != '유치원':
            handling_students = year_students[year_students.Level.str[:1] == option[:1]]
        else:
            handling_students = None

        if scale == '학생 수':
            data_color = '건수'
        elif scale == '사고 비율':
            total_students = handling_students.groupby('Region').sum()['Total Students'].to_frame().reset_index()
            total_students.columns = ['지역', '총 학생 수']
            locals = pd.merge(locals, total_students)
            locals['사고율(%)'] = round(locals['건수'] / locals['총 학생 수'] * 100, 2)
            data_color = '사고율(%)'

        choropleth = px.choropleth(locals, geojson=korea_map, locations='EMD_KOR_NM', color=data_color,
                                   color_continuous_scale='Blues', featureidkey="properties.CTP_KOR_NM")
        choropleth.update_geos(fitbounds="locations", visible=False, projection_type="orthographic")
        choropleth.update_layout(margin={"r":145,"t":0,"l":0,"b":0})
        st.plotly_chart(choropleth, config = {'displayModeBar': False}, use_container_width=True)
        col1, col2, col3 = st.columns([0.1, 1, 0.1])
        with col2:
            st.dataframe(locals.sort_values(data_color, ascending=False).head(3)[['지역', data_color]], hide_index=True,
                        column_config={'지역': st.column_config.Column(width='small'),
                            data_color: st.column_config.Column(width='medium')}, use_container_width=True)

with second_col[2]:
    with card_container(key="card"):
        st.markdown('#### 사고 유형 분석')
        variables = ['사고 당시 활동', '사고 형태', '사고 장소', '사고 부위', '사고 시간', '사고자 성별']
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            variable1 = st.selectbox(label='변인 선택 1', options=variables)
            selected1 = variable1.replace(' ', '')
            variables.remove(variable1)
        with col2:
            variable2 = st.selectbox(label='변인 선택 2', options=variables)
            selected2 = variable2.replace(' ', '')

        heatmap_data = handling_data.groupby([selected1, selected2]).size().unstack(fill_value=0)
        heatmap = px.imshow(heatmap_data, aspect="auto")
        heatmap.update_traces(hovertemplate = '사고형태: %{x}<br>사고당시활동: %{y}<br>건수: %{z:.f}<extra></extra>')
        heatmap.update_layout(margin={"r":130,"t":0,"l":0,"b":0})
        st.plotly_chart(heatmap, config = {'displayModeBar': False}, use_container_width=True)


    with card_container(key="card"):
        st.markdown('#### 사고 매개물 TOP 3 (기타 제외)')
        
        mediums = handling_data.groupby('사고매개물').count().구분.sort_values(ascending=False).drop('기타')
        top3_mediums = mediums.head(3)
        
        medium_list = ['가구', '건물', '기계', '기타', '날카로운', '열', '운동', '운송용구', '자연']
        image_list = ['desk', 'door', 'handyman', 'bubble', 'scissors', 'fire', 'ball', 'bicycle', 'person']
        selected_image = []

        for keyword in top3_mediums.index:
            for i, medium in enumerate(medium_list):
                num_of_letters = len(medium)
                if keyword[:num_of_letters] == medium[:num_of_letters]:
                    selected_image += [image_list[i]]

        for i in range(len(selected_image)):
            with card_container(key="card"):
                col1, col2 = st.columns([0.15, 0.85])
                with col1:
                    st.image(f'icons/{selected_image[i]}.svg', caption='TOP' + str(i + 1))
                with col2:
                    st.markdown(f'<h4 style="text-overflow : ellipsis; overflow: hidden; white-space: nowrap;">{top3_mediums.index[i]}</h4>', unsafe_allow_html=True)
                    st.markdown(format(top3_mediums.values[i], ',d') + '건')

    
