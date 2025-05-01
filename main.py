import streamlit as st
import pandas as pd
import pydeck as pdk
import httpx

ID = st.query_params.get('id', 0)

YAMAP_PROFILE_URL = f"https://api.yamap.com/v3/users/{ID}"
YAMAP_API_URL = f"https://api.yamap.com/v3/users/{ID}/summits"
YAMAP_USER_PAGE = f"https://yamap.com/users/{ID}"
NO_IMAGE_URL="https://image.yamap.co.jp/no_image_new.png"
PARAMS = {"page": 1, "per": 1000}
JAPAN_CENTER_LAT = 36.2048
JAPAN_CENTER_LON = 138.2529

def fetch_yamap_summits(url: str, params: dict) -> pd.DataFrame | None:
    """YAMAP APIから登頂データを取得し、座標をDataFrameで返す"""
    try:
        with httpx.Client() as client:
            response = client.get(url, params=params)
            response.raise_for_status() # HTTPエラーがあれば例外を発生させる
            data = response.json()

        summits = data.get("summits", [])

        if not summits:
            st.warning("登頂データが見つかりませんでした。")
            return None

        coords = []
        for summit in summits:
            coord = summit.get("coord")
            name = summit.get("name_ja")
            image = summit.get("image")
            small_url = None
            if image:
                small_url = image.get("small_url")

            coords.append({
                "latitude": coord[0],
                "longitude": coord[1],
                "name": name,
                "small_url": small_url if small_url else NO_IMAGE_URL
            })

        if not coords:
            st.warning("有効な座標データが見つかりませんでした。")
            return None

        return pd.DataFrame(coords)

    except httpx.RequestError as e:
        st.error(f"APIリクエストエラーが発生しました: {e}")
        return None
    except httpx.HTTPStatusError as e:
        st.error(f"APIエラーが発生しました (ステータスコード: {e.response.status_code}): {e.response.text}")
        return None
    except Exception as e:
        st.error(f"データの処理中に予期せぬエラーが発生しました: {e}")
        return None

def fetch_yamap_profile(url: str,) -> pd.DataFrame | None:
    """hoge"""
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status() # HTTPエラーがあれば例外を発生させる
        data = response.json()

    return data


if not ID:
    st.write("# yamap-peak-viewer")
    
    yamap_id = st.text_input("YAMAP ID")
    st.link_button("view", f"https://yamap-peak-viewer.streamlit.app/?id={yamap_id}")

else:
    hoge = fetch_yamap_profile(YAMAP_PROFILE_URL)
    n = hoge.get("user").get("name")
    i = hoge.get("user").get("image").get("small_url")
    a = hoge.get("user").get("activity_count")
    s = hoge.get("user").get("summit_count")

    # # 動確用
    # st.write(hoge)

    # --- Streamlit アプリ ---

    col1, col2 = st.columns([1, 5])
    with col1:
        if i: # プロフィール画像のURL (i) がある場合
            st.markdown(
                f"""
                <style>
                .profile-img {{
                    border-radius: 50%;
                    width: 100px;
                    height: 100px;
                    object-fit: cover;
                }}
                </style>
                <a href='{YAMAP_USER_PAGE}'><img src="{i}" class="profile-img"></a>
                """, unsafe_allow_html=True
            )
    with col2:
        st.title(f"{n}'s 登頂MAP")
        st.write(f"活動数：{a} / 登頂数：{s}")
    st.write("---")


    map_data = fetch_yamap_summits(YAMAP_API_URL, PARAMS)

    # ViewStateで視点を設定
    view_state = pdk.ViewState(
        latitude=JAPAN_CENTER_LAT,
        longitude=JAPAN_CENTER_LON,
        zoom=6,
        pitch=0) # pitchで地図の傾きを調整

    # ScatterplotLayerで登頂地点をプロット
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=map_data,
        get_position="[latitude, longitude]",
        get_color='[200, 30, 0, 160]', # 点の色 (RGBA)
        get_radius=5000, # 点の半径 (メートル単位)
        pickable=True, # クリックで情報を表示できるようにする
        auto_highlight=True, # ホバー時にハイライト
        id="map"
    )

    # ツールチップの設定
    tooltip = {
        "html": """
        <div style="text-align: center;">
            <strong>{name}</strong><br/>
            <img src="{small_url}" width="100" height="100" loading="lazy"/><br/>
        </div>
    """,
        "style": {
            "backgroundColor": "steelblue",
            "color": "white"
        }
    }

    deck = pdk.Deck(
        map_style=None, # マップスタイルを選択
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    )

    st.pydeck_chart(deck)
