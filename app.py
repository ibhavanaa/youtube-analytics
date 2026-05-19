import datetime
import googleapiclient.discovery
import pandas as pd
import psycopg2
import pymongo
import plotly.express as px
import plotly.io as pio
import streamlit as st
from streamlit_option_menu import option_menu

pio.templates.default = 'plotly_dark'

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


def streamlit_config():

    # page configuration
    st.set_page_config(page_title='YouTube Analytics Dashboard',
                       page_icon=':bar_chart:', layout="wide")

    # page header transparent color and high-end CSS styles
    page_background_color = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    
    /* Premium Title Style */
    .title-gradient {
        background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.25rem !important;
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 2rem;
        letter-spacing: -1px;
    }
    
    /* Premium Glassmorphic Cards */
    .metric-card {
        background: rgba(17, 24, 39, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        margin-bottom: 1.5rem;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(139, 92, 246, 0.4);
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.15);
    }
    .metric-val {
        font-size: 2.25rem;
        font-weight: 700;
        color: #f3f4f6;
        line-height: 1;
        margin-top: 0.5rem;
    }
    .metric-lbl {
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #9ca3af;
        font-weight: 600;
    }
    .query-card {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(6, 182, 212, 0.05) 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        color: #e5e7eb;
    }
    </style>
    """
    st.markdown(page_background_color, unsafe_allow_html=True)

    # title and position
    st.markdown('<div class="title-gradient">YouTube Analytics Dashboard</div>',
                unsafe_allow_html=True)


class youtube_extract:

    def channel(youtube, channel_id):

        request = youtube.channels().list(
            part='contentDetails, snippet, statistics, status',
            id=channel_id)
        response = request.execute()

        data = {'channel_name': response['items'][0]['snippet']['title'],
                'channel_id': response['items'][0]['id'],
                'subscription_count': response['items'][0]['statistics']['subscriberCount'],
                'channel_views': response['items'][0]['statistics']['viewCount'],
                'channel_description': response['items'][0]['snippet']['description'],
                'upload_id': response['items'][0]['contentDetails']['relatedPlaylists']['uploads'],
                'country': response['items'][0]['snippet'].get('country', 'Not Available')}
        return data


    def playlist(youtube, channel_id, upload_id):

        request = youtube.playlists().list(
            part="snippet,contentDetails,status",
            channelId=channel_id,
            maxResults=50)
        response = request.execute()

        playlist = []

        # Add the default Uploads playlist containing all uploaded videos
        playlist.append({
            'playlist_id': upload_id,
            'playlist_name': 'Uploads',
            'channel_id': channel_id,
            'upload_id': upload_id
        })

        for i in range(0, len(response['items'])):
            data = {'playlist_id': response['items'][i]['id'],
                    'playlist_name': response['items'][i]['snippet']['title'],
                    'channel_id': channel_id,
                    'upload_id': upload_id}

            playlist.append(data)

        next_page_token = response.get('nextPageToken')

        # manually set umbrella = True for breaking while condition
        umbrella = True

        while umbrella:
            if next_page_token is None:
                umbrella = False

            else:
                request = youtube.playlists().list(
                    part="snippet,contentDetails,status",
                    channelId=channel_id,
                    maxResults=50,
                    pageToken=next_page_token)
                response = request.execute()

                for i in range(0, len(response['items'])):
                    data = {'playlist_id': response['items'][i]['id'],
                            'playlist_name': response['items'][i]['snippet']['title'],
                            'channel_id': channel_id,
                            'upload_id': upload_id}

                    playlist.append(data)

                next_page_token = response.get('nextPageToken')

        return playlist


    def video_ids(youtube, upload_id):

        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=upload_id,
            maxResults=50)
        response = request.execute()

        video_ids = []

        for i in range(0, len(response['items'])):
            data = response['items'][i]['contentDetails']['videoId']
            video_ids.append(data)

        next_page_token = response.get('nextPageToken')

        # manually set umbrella = True for breaking while condition
        umbrella = True

        while umbrella:
            if next_page_token is None:
                umbrella = False

            else:
                request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=upload_id,
                    maxResults=50,
                    pageToken=next_page_token)
                response = request.execute()

                for i in range(0, len(response['items'])):
                    data = response['items'][i]['contentDetails']['videoId']
                    video_ids.append(data)

                next_page_token = response.get('nextPageToken')

        return video_ids


    def video(youtube, video_id, upload_id):

        request = youtube.videos().list(
            part='contentDetails, snippet, statistics',
            id=video_id)
        response = request.execute()

        caption = {'true': 'Available', 'false': 'Not Available'}

        # convert PT15M33S to 00:15:33 format using Timedelta function in pandas

        def time_duration(t):
            a = pd.Timedelta(t)
            b = str(a).split()[-1]
            return b

        data = {'video_id': response['items'][0]['id'],
                'video_name': response['items'][0]['snippet']['title'],
                'video_description': response['items'][0]['snippet']['description'],
                'upload_id': upload_id,
                'tags': response['items'][0]['snippet'].get('tags', []),
                'published_date': response['items'][0]['snippet']['publishedAt'][0:10],
                'published_time': response['items'][0]['snippet']['publishedAt'][11:19],
                'view_count': response['items'][0]['statistics']['viewCount'],
                'like_count': response['items'][0]['statistics'].get('likeCount', 0),
                'favourite_count': response['items'][0]['statistics']['favoriteCount'],
                'comment_count': response['items'][0]['statistics'].get('commentCount', 0),
                'duration': time_duration(response['items'][0]['contentDetails']['duration']),
                'thumbnail': response['items'][0]['snippet']['thumbnails']['default']['url'],
                'caption_status': caption[response['items'][0]['contentDetails']['caption']]}

        if data['tags'] == []:
            del data['tags']

        return data


    def comment(youtube, video_id):

        request = youtube.commentThreads().list(
            part='id, snippet',
            videoId=video_id,
            maxResults=100)
        response = request.execute()

        comment = []

        for i in range(0, len(response['items'])):
            data = {'comment_id': response['items'][i]['id'],
                    'comment_text': response['items'][i]['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'comment_author': response['items'][i]['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'comment_published_date': response['items'][i]['snippet']['topLevelComment']['snippet']['publishedAt'][0:10],
                    'comment_published_time': response['items'][i]['snippet']['topLevelComment']['snippet']['publishedAt'][11:19],
                    'video_id': video_id}
            
            comment.append(data)

        return comment


    def main(channel_id, video_limit=10):

        channel = youtube_extract.channel(youtube, channel_id)
        upload_id = channel['upload_id']
        playlist = youtube_extract.playlist(youtube, channel_id, upload_id)
        video_ids = youtube_extract.video_ids(youtube, upload_id)
        
        # Limit the number of videos harvested
        video_ids = video_ids[:video_limit]

        video = []
        comment = []

        for i in video_ids:
            v = youtube_extract.video(youtube, i, upload_id)
            video.append(v)

            # skip disabled comments error in looping function
            try:
                c = youtube_extract.comment(youtube, i)
                comment.append(c)
            except:
                pass

        final = {'channel': channel,
                 'playlist': playlist,
                 'video': video,
                 'comment': comment}

        return final


    def display_sample_data(channel_id, video_limit=10):

        channel = youtube_extract.channel(youtube, channel_id)
        upload_id = channel['upload_id']
        playlist = youtube_extract.playlist(youtube, channel_id, upload_id)
        video_ids = youtube_extract.video_ids(youtube, upload_id)
        
        # Limit the videos processed
        video_ids = video_ids[:video_limit]

        video = []
        comment = []

        for i in video_ids:
            v = youtube_extract.video(youtube, i, upload_id)
            video.append(v)

            # skip disabled comments error in looping function
            try:
                c = youtube_extract.comment(youtube, i)
                comment.append(c)
            except:
                pass
            break

        final = {'channel': channel,
                 'playlist': playlist,
                 'video': video,
                 'comment': comment}

        return final


class mongodb:
  
    def data_storage(channel_name, database, data):
        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client[database]
        col = db[channel_name]
        col.insert_one(data)


    def list_collection_names(database):
        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client[database]
        col = db.list_collection_names()
        col.sort(reverse=False)
        return col


    def order_collection_names(database):

        m = mongodb.list_collection_names(database)

        if m == []:
            st.info("The Mongodb database is currently empty")

        else:
            st.subheader('List of collections in MongoDB database')
            m = mongodb.list_collection_names(database)
            c = 1
            for i in m:
                st.write(str(c) + ' - ' + i)
                c += 1


    def drop_temp_collection():
        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client['temp']
        col = db.list_collection_names()
        if len(col) > 0:
            for i in col:
                db.drop_collection(i)


    def main(database):

        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client['temp']
        col = db.list_collection_names()

        if len(col) == 0:
            st.info("There is no data retrived from youtube")

        else:
            client = pymongo.MongoClient(st.secrets["MONGO_URI"])
            db = client['temp']
            col = db.list_collection_names()
            channel_name = col[0]

            # Now we get the channel name and access channel data
            data_youtube = {}
            col1 = db[channel_name]
            for i in col1.find():
                data_youtube.update(i)

            # verify channel name already exists in database
            list_collection_names = mongodb.list_collection_names(database)

            if channel_name not in list_collection_names:
                mongodb.data_storage(channel_name, database, data_youtube)
                st.success(
                    "The data has been successfully stored in the MongoDB database")
                st.balloons()
                mongodb.drop_temp_collection()

            else:
                st.warning(
                    "The data has already been stored in MongoDB database")
                option = st.radio('Do you want to overwrite the data currently stored?',
                                  ['Select one below', 'Yes', 'No'])

                if option == 'Yes':
                    client = pymongo.MongoClient(st.secrets["MONGO_URI"])
                    db = client[database]

                    # delete existing data
                    db[channel_name].drop()

                    # add new data
                    mongodb.data_storage(channel_name, database, data_youtube)
                    st.success(
                        "The data has been successfully overwritten and updated in MongoDB database")
                    st.balloons()
                    mongodb.drop_temp_collection()

                elif option == 'No':
                    mongodb.drop_temp_collection()
                    st.info("The data overwrite process has been skipped")


class sql:

    def create_tables():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""create table if not exists channel(
                                    channel_id 			varchar(255) primary key,
                                    channel_name		varchar(255),
                                    subscription_count	bigint,
                                    channel_views		bigint,
                                    channel_description	text,
                                    upload_id			varchar(255),
                                    country				varchar(255));""")

        cursor.execute(f"""create table if not exists playlist(
                                    playlist_id		varchar(255) primary key,
                                    playlist_name	varchar(255),
                                    channel_id		varchar(255),
                                    upload_id		varchar(255));""")

        cursor.execute(f"""create table if not exists video(
                                    video_id			varchar(255) primary key,
                                    video_name			varchar(255),
                                    video_description	text,
                                    upload_id			varchar(255),
                                    tags				text,
                                    published_date		date,
                                    published_time		time,
                                    view_count			bigint,
                                    like_count			bigint,
                                    favourite_count		bigint,
                                    comment_count		bigint,
                                    duration			time,
                                    thumbnail			varchar(255),
                                    caption_status		varchar(255));""")

        cursor.execute(f"""create table if not exists comment(
                                    comment_id				varchar(255) primary key,
                                    comment_text			text,
                                    comment_author			varchar(255),
                                    comment_published_date	date,
                                    comment_published_time	time,
                                    video_id				varchar(255));""")

        conn.commit()

        # Self-healing migration block: dynamically convert existing columns to bigint to support large values
        try:
            cursor.execute("ALTER TABLE channel ALTER COLUMN subscription_count TYPE bigint;")
            cursor.execute("ALTER TABLE channel ALTER COLUMN channel_views TYPE bigint;")
            cursor.execute("ALTER TABLE video ALTER COLUMN view_count TYPE bigint;")
            cursor.execute("ALTER TABLE video ALTER COLUMN like_count TYPE bigint;")
            cursor.execute("ALTER TABLE video ALTER COLUMN favourite_count TYPE bigint;")
            cursor.execute("ALTER TABLE video ALTER COLUMN comment_count TYPE bigint;")
            conn.commit()
        except:
            conn.rollback()

        conn.close()


    def list_channel_names():
        try:
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()
            cursor.execute("select channel_name from channel")
            s = cursor.fetchall()
            s = [i[0] for i in s]
            s.sort(reverse=False)
            conn.close()
            return s
        except:
            return []


    def order_channel_names():
        try:
            s = sql.list_channel_names()
            if s == []:
                st.info("The SQL database is currently empty")
            else:
                st.subheader("List of channels in SQL database")
                c = 1
                for i in s:
                    st.write(str(c) + ' - ' + i)
                    c += 1
        except:
            st.info("The SQL database is currently empty")


    def channel(database, channel_name):

        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client[database]
        col = db[channel_name]

        data = []
        for i in col.find({}, {'_id': 0, 'channel': 1}):
            data.append(i['channel'])

        df = pd.DataFrame(data)
        df = df.reindex(columns=['channel_id', 'channel_name', 'subscription_count', 'channel_views',
                                 'channel_description', 'upload_id', 'country'])
        df['subscription_count'] = pd.to_numeric(df['subscription_count'])
        df['channel_views'] = pd.to_numeric(df['channel_views'])
        df = df.where(pd.notnull(df), None)
        return df


    def playlist(database, channel_name):

        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client[database]
        col = db[channel_name]

        data = []
        for i in col.find({}, {'_id': 0, 'playlist': 1}):
            if 'playlist' in i and isinstance(i['playlist'], list):
                data.extend(i['playlist'])

        # If data is empty, let's synthesize the default 'Uploads' playlist!
        channel_doc = col.find_one({}, {'_id': 0, 'channel': 1})
        if channel_doc and 'channel' in channel_doc:
            ch = channel_doc['channel']
            upload_id = ch.get('upload_id')
            channel_id = ch.get('channel_id')
            
            # Check if this uploads playlist is in data
            has_uploads = any(p.get('playlist_id') == upload_id for p in data if isinstance(p, dict))
            if not has_uploads and upload_id:
                data.append({
                    'playlist_id': upload_id,
                    'playlist_name': 'Uploads',
                    'channel_id': channel_id,
                    'upload_id': upload_id
                })

        df = pd.DataFrame(data)
        df = df.reindex(
            columns=['playlist_id', 'playlist_name', 'channel_id', 'upload_id'])
        df = df.where(pd.notnull(df), None)
        return df


    def video(database, channel_name):

        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client[database]
        col = db[channel_name]

        data = []
        for i in col.find({}, {'_id': 0, 'video': 1}):
            data.extend(i['video'])

        df = pd.DataFrame(data)
        df = df.reindex(columns=['video_id', 'video_name', 'video_description', 'upload_id',
                                 'tags', 'published_date', 'published_time', 'view_count',
                                 'like_count', 'favourite_count', 'comment_count', 'duration',
                                 'thumbnail', 'caption_status'])

        df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce').dt.date
        df['published_time'] = pd.to_datetime(
            df['published_time'], format='%H:%M:%S', errors='coerce').dt.time
        df['view_count'] = pd.to_numeric(df['view_count'])
        df['like_count'] = pd.to_numeric(df['like_count'])
        df['favourite_count'] = pd.to_numeric(df['favourite_count'])
        df['comment_count'] = pd.to_numeric(df['comment_count'])
        df['duration'] = pd.to_datetime(
            df['duration'], format='%H:%M:%S', errors='coerce').dt.time
        
        # Convert tags list to a comma-separated string to avoid psycopg2 type adapter crashes
        df['tags'] = df['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x) if pd.notnull(x) else None)
        df = df.where(pd.notnull(df), None)
        return df


    def comment(database, channel_name):
        client = pymongo.MongoClient(st.secrets["MONGO_URI"])
        db = client[database]
        col = db[channel_name]

        data = []
        for i in col.find({}, {'_id': 0, 'comment': 1}):
            if 'comment' in i and isinstance(i['comment'], list):
                for sublist in i['comment']:
                    if isinstance(sublist, list):
                        data.extend(sublist)
                    elif isinstance(sublist, dict):
                        data.append(sublist)

        if not data:
            return pd.DataFrame(columns=['comment_id', 'comment_text', 'comment_author',
                                         'comment_published_date', 'comment_published_time', 'video_id'])

        df = pd.DataFrame(data)
        df = df.reindex(columns=['comment_id', 'comment_text', 'comment_author',
                                 'comment_published_date', 'comment_published_time', 'video_id'])
        df['comment_published_date'] = pd.to_datetime(
            df['comment_published_date'], errors='coerce').dt.date
        df['comment_published_time'] = pd.to_datetime(
            df['comment_published_time'], format='%H:%M:%S', errors='coerce').dt.time
        df = df.where(pd.notnull(df), None)
        return df


    def main(mdb_database, sql_database):

        # create table in sql
        sql.create_tables()

        # mongodb and sql channel names
        m = mongodb.list_collection_names(mdb_database)
        s = sql.list_channel_names()

        if s == m == []:
            st.info("Both Mongodb and SQL databases are currently empty")

        else:
            # mongodb and sql channel names
            mongodb.order_collection_names(mdb_database)
            sql.order_channel_names()

            # all harvested channels in MongoDB for migration or sync
            list_mongodb_notin_sql = ['Select one']
            m = mongodb.list_collection_names(mdb_database)

            # Show all MongoDB collections so you can re-run/sync them anytime
            for i in m:
                list_mongodb_notin_sql.append(i)

            # channel name for user selection
            option = st.selectbox('', list_mongodb_notin_sql)

            if option == 'Select one':
                col1, col2 = st.columns(2)
                with col1:
                    st.warning('Please select the channel')

            else:
                channel = sql.channel(mdb_database, option)
                playlist = sql.playlist(mdb_database, option)
                video = sql.video(mdb_database, option)
                comment = sql.comment(mdb_database, option)

                conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
                cursor = conn.cursor()

                if not channel.empty:
                    cursor.executemany(f"""insert into channel(channel_id, channel_name, subscription_count,
                                            channel_views, channel_description, upload_id, country) 
                                            values(%s,%s,%s,%s,%s,%s,%s)
                                            ON CONFLICT (channel_id) DO NOTHING""", channel.values.tolist())

                if not playlist.empty:
                    cursor.executemany(f"""insert into playlist(playlist_id, playlist_name, channel_id, 
                                            upload_id) 
                                            values(%s,%s,%s,%s)
                                            ON CONFLICT (playlist_id) DO NOTHING""", playlist.values.tolist())

                if not video.empty:
                    cursor.executemany(f"""insert into video(video_id, video_name, video_description, 
                                            upload_id, tags, published_date, published_time, view_count, 
                                            like_count, favourite_count, comment_count, duration, thumbnail, 
                                            caption_status) 
                                            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                            ON CONFLICT (video_id) DO NOTHING""",
                                       video.values.tolist())

                if not comment.empty:
                    cursor.executemany(f"""insert into comment(comment_id, comment_text, comment_author, 
                                            comment_published_date, comment_published_time, video_id) 
                                            values(%s,%s,%s,%s,%s,%s)
                                            ON CONFLICT (comment_id) DO NOTHING""", comment.values.tolist())

                conn.commit()
                st.success("Migrated Data Successfully to SQL Data Warehouse")
                st.balloons()
                conn.close()


class sql_queries:

    def q1_allvideoname_channelname():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        
        cursor = conn.cursor()

        # using Inner Join to join the tables
        cursor.execute(f'''select video.video_name, channel.channel_name
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            group by video.video_id, channel.channel_id
                            order by channel.channel_name ASC''')
        
        s = cursor.fetchall()

        # add index for dataframe and set a column names
        i = [i for i in range(1, len(s) + 1)]
        data = pd.DataFrame(s, columns=['Video Names', 'Channel Names'], index=i)

        # add name for 'S.No'
        data = data.rename_axis('S.No')

        # index in center position of dataframe
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

        return data


    def q2_channelname_totalvideos():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f'''select distinct channel.channel_name, count(distinct video.video_id) as total
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by channel.channel_id
                        order by total DESC''')
        
        s = cursor.fetchall()

        i = [i for i in range(1, len(s) + 1)]
        data = pd.DataFrame(s, columns=['Channel Names', 'Total Videos'], index=i)

        data = data.rename_axis('S.No')
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

        return data


    def q3_mostviewvideos_channelname():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f'''select distinct video.video_name, video.view_count, channel.channel_name
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            order by video.view_count DESC
                            limit 10''')
        
        s = cursor.fetchall()

        i = [i for i in range(1, len(s) + 1)]
        data = pd.DataFrame(s, columns=['Video Names', 'Total Views', 'Channel Names'], index=i)

        data = data.rename_axis('S.No')
        data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

        return data


    def q4_videonames_totalcomments():
            
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()

            cursor.execute(f'''select video.video_name, video.comment_count, channel.channel_name
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            group by video.video_id, channel.channel_name
                            order by video.comment_count DESC''')
            
            s = cursor.fetchall()

            i = [i for i in range(1, len(s) + 1)]
            data = pd.DataFrame(s, columns=['Video Names', 'Total Comments', 'Channel Names'], index=i)

            data = data.rename_axis('S.No')
            data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

            return data


    def q5_videonames_highestlikes_channelname():
            
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()

            cursor.execute(f'''select distinct video.video_name, channel.channel_name, video.like_count
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            where video.like_count = (select max(like_count) from video)''')
            
            s = cursor.fetchall()

            i = [i for i in range(1, len(s) + 1)]
            data = pd.DataFrame(s, columns=['Video Names', 'Channel Names', 'Most Likes'], index=i)

            data = data.reindex(columns=['Video Names', 'Most Likes', 'Channel Names'])
            data = data.rename_axis('S.No')
            data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

            return data


    def q6_videonames_totallikes_channelname():
            
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()

            cursor.execute(f'''select distinct video.video_name, video.like_count, channel.channel_name
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            group by video.video_id, channel.channel_id
                            order by video.like_count DESC''')
            
            s = cursor.fetchall()

            i = [i for i in range(1, len(s) + 1)]
            data = pd.DataFrame(s, columns=['Video Names', 'Total Likes', 'Channel Names'], index=i)

            data = data.rename_axis('S.No')
            data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))
            
            return data


    def q7_channelnames_totalviews():
            
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()

            cursor.execute(f'''select channel_name, channel_views from channel
                            order by channel_views DESC''')
            
            s = cursor.fetchall()

            i = [i for i in range(1, len(s) + 1)]
            data = pd.DataFrame(s, columns=['Channel Names', 'Total Views'], index=i)
            
            data = data.rename_axis('S.No')
            data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

            return data


    def q8_channelnames_releasevideos(year):
            
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()

            cursor.execute(f"""select distinct channel.channel_name, count(distinct video.video_id) as total
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            where extract(year from video.published_date) = '{year}'
                            group by channel.channel_id
                            order by total DESC""")
            
            s = cursor.fetchall()

            i = [i for i in range(1, len(s) + 1)]
            data = pd.DataFrame(s, columns=['Channel Names', 'Published Videos'], index=i)

            data = data.rename_axis('S.No')
            data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))
            
            return data


    def q9_channelnames_avgvideoduration():
            
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()

            cursor.execute(f'''select channel.channel_name, avg(video.duration - time '00:00:00') as average
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            group by channel.channel_id, channel.channel_name
                            order by average DESC''')
            
            s = cursor.fetchall()

            i = [i for i in range(1, len(s) + 1)]
            data = pd.DataFrame(s, columns=['Channel Names', 'Average Video Duration'], index=i)
            data['Average Video Duration'] = data['Average Video Duration'].apply(
                lambda x: str(x).split('.')[0] if pd.notnull(x) else "00:00:00")
            
            data = data.rename_axis('S.No')
            data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

            return data


    def q10_videonames_channelnames_mostcomments():
            
            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
            cursor = conn.cursor()

            cursor.execute(f'''select video.video_name, video.comment_count, channel.channel_name
                            from video
                            inner join playlist on playlist.upload_id = video.upload_id
                            inner join channel on channel.channel_id = playlist.channel_id
                            group by video.video_id, channel.channel_name
                            order by video.comment_count DESC
                            limit 1''')
            
            s = cursor.fetchall()

            i = [i for i in range(1, len(s) + 1)]
            data = pd.DataFrame(s, columns=['Video Names', 'Channel Names', 'Total Comments'], index=i)

            data = data.rename_axis('S.No')
            data.index = data.index.map(lambda x: '{:^{}}'.format(x, 10))

            return data


    def main():
        st.markdown('<div class="query-card">💡 select a query from the dropdown to run real-time analytical SQL queries on your PostgreSQL database and visualize the results instantly in highly interactive charts!</div>', unsafe_allow_html=True)
        
        q1 = 'Q1-What are the names of all the videos and their corresponding channels?'
        q2 = 'Q2-Which channels have the most number of videos, and how many videos do they have?'
        q3 = 'Q3-What are the top 10 most viewed videos and their respective channels?'
        q4 = 'Q4-How many comments were made on each video with their corresponding video names?'
        q5 = 'Q5-Which videos have the highest number of likes with their corresponding channel names?'
        q6 = 'Q6-What is the total number of likes for each video with their corresponding video names?'
        q7 = 'Q7-What is the total number of views for each channel with their corresponding channel names?'
        q8 = 'Q8-What are the names of all the channels that have published videos in the particular year?'
        q9 = 'Q9-What is the average duration of all videos in each channel with corresponding channel names?'
        q10 = 'Q10-Which videos have the highest number of comments with their corresponding channel names?'

        query_option = st.selectbox(
            'Select a query to execute:', ['Select One', q1, q2, q3, q4, q5, q6, q7, q8, q9, q10])

        if query_option == q1:
            df = sql_queries.q1_allvideoname_channelname()
            if not df.empty:
                # Donut chart of video count distribution per channel
                st.subheader("📊 Videos Distribution by Channel")
                channel_counts = df['Channel Names'].value_counts().reset_index()
                channel_counts.columns = ['Channel Name', 'Video Count']
                fig = px.pie(channel_counts, names='Channel Name', values='Video Count', hole=0.5,
                             color_discrete_sequence=px.colors.sequential.Agsunset)
                fig.update_traces(textinfo='percent+label', textposition='outside')
                fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20), height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q2:
            df = sql_queries.q2_channelname_totalvideos()
            if not df.empty:
                st.subheader("📊 Channels by Number of Videos")
                fig = px.bar(df, x='Total Videos', y='Channel Names', orientation='h',
                             color='Total Videos', color_continuous_scale='purples')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q3:
            df = sql_queries.q3_mostviewvideos_channelname()
            if not df.empty:
                st.subheader("🏆 Top 10 Most Viewed Videos")
                fig = px.bar(df.head(10), x='Total Views', y='Video Names', orientation='h',
                             color='Total Views', color_continuous_scale='Tealgrn')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False, height=450)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q4:
            df = sql_queries.q4_videonames_totalcomments()
            if not df.empty:
                st.subheader("💬 Comment Count by Video")
                fig = px.bar(df, x='Video Names', y='Total Comments', 
                             color='Total Comments', color_continuous_scale='Viridis')
                fig.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False, height=450)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q5:
            df = sql_queries.q5_videonames_highestlikes_channelname()
            if not df.empty:
                st.subheader("❤️ Videos with Highest Likes")
                fig = px.bar(df, x='Total Likes', y='Video Names', orientation='h',
                             color='Total Likes', color_continuous_scale='sunset')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False, height=450)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q6:
            df = sql_queries.q6_videonames_totallikes_channelname()
            if not df.empty:
                st.subheader("📊 Engagement Matrix: Likes count per Video")
                fig = px.bar(df, x='Video Names', y='Total Likes',
                             color='Total Likes', color_continuous_scale='Bluered')
                fig.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False, height=450)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q7:
            df = sql_queries.q7_channelnames_totalviews()
            if not df.empty:
                st.subheader("🌎 Total Views Share by Channel")
                fig = px.pie(df, names='Channel Names', values='Total Views', hole=0.6,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(textinfo='percent+label', textposition='outside')
                fig.update_layout(showlegend=True, margin=dict(t=20, b=20, l=20, r=20), height=450)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q8:
            col1, col2 = st.columns([1, 2])
            with col1:
                year = st.text_input('Enter the release year (e.g. 2018 or 2026):', value="2018")
                submit = st.button('Execute Query')
            
            if submit:
                df = sql_queries.q8_channelnames_releasevideos(year)
                with col2:
                    if not df.empty:
                        st.subheader(f"📅 Channels Active in {year}")
                        for channel_name in df['Channel Names']:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-lbl">📅 Published in {year}</div>
                                <div class="metric-val" style="font-size:1.75rem; color:#8b5cf6;">🎥 {channel_name}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with st.expander("📋 View Raw Tabular Data"):
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.warning(f"No channels published any videos in the year {year}.")

        elif query_option == q9:
            df = sql_queries.q9_channelnames_avgvideoduration()
            if not df.empty:
                st.subheader("⏳ Average Video Duration by Channel")
                # Parse average duration (HH:MM:SS) to total minutes for a cleaner visualization
                def to_minutes(time_str):
                    try:
                        parts = str(time_str).split(':')
                        return int(parts[0]) * 60 + int(parts[1]) + float(parts[2])/60.0
                    except:
                        return 0.0
                
                df_viz = df.copy()
                df_viz['Average Minutes'] = df_viz['Average Durations'].apply(to_minutes)
                
                fig = px.bar(df_viz, x='Average Minutes', y='Channel Names', orientation='h',
                             color='Average Minutes', color_continuous_scale='dense')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")

        elif query_option == q10:
            df = sql_queries.q10_videonames_channelnames_mostcomments()
            if not df.empty:
                st.subheader("🔥 Most Commented Video of All Time")
                row = df.iloc[0]
                st.markdown(f"""
                <div class="metric-card" style="border: 2px solid rgba(236, 72, 153, 0.4); background: linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);">
                    <div class="metric-lbl" style="color:#ec4899; font-weight:800;">🏆 WINNING VIDEO</div>
                    <div class="metric-val" style="font-size:2rem; margin-bottom:1rem; color:#f3f4f6;">🎬 "{row['Video Names']}"</div>
                    <hr style="opacity:0.1; margin:1rem 0;"/>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div class="metric-lbl">📡 CHANNEL</div>
                            <div style="font-size:1.25rem; font-weight:600; color:#8b5cf6;">📺 {row['Channel Names']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="metric-lbl">💬 TOTAL COMMENTS</div>
                            <div class="metric-val" style="font-size:2.5rem; color:#06b6d4; margin-top:0;">{row['Total Comments']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📋 View Raw Tabular Data"):
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available.")


class channel_analysis:

    def total_channel_names():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(
            "select channel_name from channel order by channel_name ASC")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(s, columns=['Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_playlist_names():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select distinct playlist.playlist_name, channel.channel_name
                        from playlist
                        inner join channel on playlist.channel_id = channel.channel_id
                        group by playlist.playlist_name, channel.channel_name
                        order by channel.channel_name, playlist.playlist_name ASC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Playlist Names', 'Channel Names'], index=i)
        df = df.reindex(columns=['Channel Names', 'Playlist Names'])
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_playlist_names_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select distinct playlist.playlist_name, channel.channel_name
                            from playlist
                            inner join channel on playlist.channel_id = channel.channel_id
                            where channel.channel_name='{channel_name}'
                            group by playlist.playlist_id, channel.channel_name
                            order by channel.channel_name, playlist.playlist_name ASC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Playlist Names', 'Channel Names'], index=i)
        df = df.reindex(columns=['Channel Names', 'Playlist Names'])
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_playlist_count():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select distinct channel.channel_name, count(distinct playlist.playlist_id) as total
                        from playlist
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by channel.channel_id
                        order by total DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Channel Names', 'Total Playlists'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_video_count():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select channel.channel_name, count(distinct video.video_id) as total
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by channel.channel_id
                        order by total DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Channel Names', 'Total Videos'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def published_videos_count(start_date, end_date):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select distinct channel.channel_name, count(distinct video.video_id) as total
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where video.published_date between '{start_date}' and '{end_date}'
                        group by channel.channel_id
                        order by total DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Channel Names', 'Published videos'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_subscriptions():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select channel_name, subscription_count 
                           from channel
                           order by subscription_count DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Channel Names', 'Total Subscriptions'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_views():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select channel_name, channel_views 
                           from channel
                           order by channel_views DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(s, columns=['Channel Names', 'Total Views'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_likes():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select distinct channel.channel_name, cast(sum(subquery.sum1) as bigint) as sum2
                        from channel
                        inner join(select distinct playlist.channel_id, video.video_id, sum(distinct video.like_count) as sum1
                        from playlist
                        inner join video on playlist.upload_id = video.upload_id
                        group by playlist.channel_id, video.video_id
                        )as subquery on subquery.channel_id = channel.channel_id
                        group by channel.channel_name
                        order by sum2 DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(s, columns=['Channel Names', 'Total Likes'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_comments():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select distinct channel.channel_name, count(distinct comment.comment_id) as total
                        from comment
                        inner join video on video.video_id = comment.video_id
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by channel.channel_name
                        order by total DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Channel Names', 'Total Comments'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    # convert days with time to HH:MM:SS

    def convert_durations(durations):
        try:
            if 'day' in durations:
                parts = durations.split(' day ') if ' day ' in durations else durations.split(' days ')
                days = int(parts[0])
                time_str = parts[1]
            else:
                days = 0
                time_str = durations
            
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(float(parts[2]))
            
            total_hours = days * 24 + hours
            return f"{total_hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception as e:
            return "00:00:00"

    def total_durations():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select channel.channel_name, sum(video.duration - time '00:00:00') as total
                        from video
                        inner join channel on channel.upload_id = video.upload_id
                        group by channel.channel_id, channel.channel_name
                        order by total DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Channel Names', 'Total Durations'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        df['Total Durations'] = df['Total Durations'].apply(
            lambda x: channel_analysis.convert_durations(str(x)) if pd.notnull(x) else "00:00:00")
        return df

    def average_durations():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select channel.channel_name, avg(video.duration - time '00:00:00') as average
                           from video
                           inner join channel on channel.upload_id = video.upload_id
                           group by channel.channel_id, channel.channel_name
                           order by average DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Channel Names', 'Average Durations'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        df['Average Durations'] = df['Average Durations'].apply(
            lambda x: str(x).split('.')[0] if pd.notnull(x) else "00:00:00")
        return df

    def main():
        # High-impact tabbed layout for channel analytics
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Overview Dashboard", 
            "🎥 Playlists & Videos", 
            "👁️ Views & Subscriptions", 
            "❤️ Engagement & Durations"
        ])

        with tab1:
            st.markdown("### 📊 Channels High-Level Summary")
            df_subs = channel_analysis.total_subscriptions()
            df_views = channel_analysis.total_views()
            df_vids = channel_analysis.total_video_count()

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-lbl">📡 TOTAL CHANNELS</div>
                    <div class="metric-val" style="color: #ec4899;">{len(df_subs)}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                total_subs = df_subs['Total Subscriptions'].sum() if not df_subs.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-lbl">👥 TOTAL AUDIENCE</div>
                    <div class="metric-val" style="color: #8b5cf6;">{total_subs:,}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_c:
                total_views = df_views['Total Views'].sum() if not df_views.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-lbl">👁️ TOTAL VIEWS</div>
                    <div class="metric-val" style="color: #06b6d4;">{total_views:,}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_d:
                total_videos = df_vids['Total Videos'].sum() if not df_vids.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-lbl">🎥 TOTAL VIDEOS</div>
                    <div class="metric-val" style="color: #10b981;">{total_videos}</div>
                </div>
                """, unsafe_allow_html=True)

            # Channel list card style
            st.markdown("#### 📺 Harvested Channels")
            ch_names = channel_analysis.total_channel_names()
            st.dataframe(ch_names, use_container_width=True)

        with tab2:
            st.markdown("### 📁 Playlists & Uploads Volume")
            
            # Channel wise Playlist Names and Select Box
            col1, col2 = st.columns(2)
            with col1:
                st.subheader('Channel wise Playlists list')
                channel = st.selectbox('Select Channel to view Playlists:', list_channel, key="ch_playlist_select")
                if channel == 'Over All':
                    st.dataframe(channel_analysis.total_playlist_names(), use_container_width=True)
                else:
                    st.dataframe(channel_analysis.total_playlist_names_select_channel(channel), use_container_width=True)

            with col2:
                # Playlist counts pie chart
                st.subheader('Playlists Distribution Share')
                df_pl = channel_analysis.total_playlist_count()
                if not df_pl.empty:
                    fig = px.pie(df_pl, names='Channel Names', values='Total Playlists', hole=0.5,
                                 color_discrete_sequence=px.colors.sequential.Agsunset)
                    fig.update_traces(textinfo='percent+label', textposition='outside')
                    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No playlists harvested.")

            st.markdown("---")
            
            # Video Count bar chart
            st.subheader('🎥 Total Videos Count by Channel')
            df_v = channel_analysis.total_video_count()
            if not df_v.empty:
                df_v_sorted = df_v.sort_values(by='Total Videos', ascending=True)
                fig = px.bar(df_v_sorted, x='Total Videos', y='Channel Names', orientation='h',
                             color='Total Videos', color_continuous_scale='sunset')
                fig.update_layout(coloraxis_showscale=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No videos harvested.")

            st.markdown("---")

            # Date wise Published Videos
            st.subheader('📅 Video Publishing Frequency by Date Range')
            current_date = datetime.datetime.now().date()
            current_year = datetime.datetime.now().year
            year_startdate = datetime.date(current_year, 1, 1)

            c_date1, c_date2 = st.columns(2)
            with c_date1:
                start_date = st.date_input('Start Date', value=year_startdate, key="ch_start_date")
            with c_date2:
                end_date = st.date_input('End Date', value=current_date, max_value=current_date, key="ch_end_date")

            df_pub = channel_analysis.published_videos_count(start_date, end_date)
            if not df_pub.empty:
                df_pub_sorted = df_pub.sort_values(by='Published videos', ascending=True)
                fig = px.bar(df_pub_sorted, x='Published videos', y='Channel Names', orientation='h',
                             color='Published videos', color_continuous_scale='Mint')
                fig.update_layout(coloraxis_showscale=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
                with st.expander("📋 View Publishing Count Table"):
                    st.dataframe(df_pub, use_container_width=True)
            else:
                st.info("No videos published in this date range.")

        with tab3:
            st.markdown("### 👁️ Audience Engagement Share")
            
            col_views, col_subs = st.columns(2)
            with col_views:
                st.subheader('Total Views per Channel')
                df_vws = channel_analysis.total_views()
                if not df_vws.empty:
                    df_vws_sorted = df_vws.sort_values(by='Total Views', ascending=True)
                    fig = px.bar(df_vws_sorted, x='Total Views', y='Channel Names', orientation='h',
                                 color='Total Views', color_continuous_scale='Tealgrn')
                    fig.update_layout(coloraxis_showscale=False, height=350)
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Views Table"):
                        st.dataframe(df_vws, use_container_width=True)
                else:
                    st.info("No views data.")

            with col_subs:
                st.subheader('Subscriber Count Share')
                df_sb = channel_analysis.total_subscriptions()
                if not df_sb.empty:
                    fig = px.pie(df_sb, names='Channel Names', values='Total Subscriptions', hole=0.5,
                                 color_discrete_sequence=px.colors.sequential.Sunsetdark)
                    fig.update_traces(textinfo='percent+label', textposition='outside')
                    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Subscriber Table"):
                        st.dataframe(df_sb, use_container_width=True)
                else:
                    st.info("No subscriber data.")

        with tab4:
            st.markdown("### ❤️ Engagement Metrics & Video Lengths")
            
            col_likes, col_comments = st.columns(2)
            with col_likes:
                st.subheader('Likes Share by Channel')
                df_lk = channel_analysis.total_likes()
                if not df_lk.empty:
                    fig = px.pie(df_lk, names='Channel Names', values='Total Likes', hole=0.5,
                                 color_discrete_sequence=px.colors.sequential.Agsunset)
                    fig.update_traces(textinfo='percent+label', textposition='outside')
                    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Likes Table"):
                        st.dataframe(df_lk, use_container_width=True)
                else:
                    st.info("No likes data.")

            with col_comments:
                st.subheader('Comments Count by Channel')
                df_cm = channel_analysis.total_comments()
                if not df_cm.empty:
                    df_cm_sorted = df_cm.sort_values(by='Total Comments', ascending=True)
                    fig = px.bar(df_cm_sorted, x='Total Comments', y='Channel Names', orientation='h',
                                 color='Total Comments', color_continuous_scale='dense')
                    fig.update_layout(coloraxis_showscale=False, height=350)
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Comments Table"):
                        st.dataframe(df_cm, use_container_width=True)
                else:
                    st.info("No comments data.")

            st.markdown("---")

            col_dur, col_avg_dur = st.columns(2)
            with col_dur:
                st.subheader('Total Content Duration')
                df_tdur = channel_analysis.total_durations()
                if not df_tdur.empty:
                    df_tdur_viz = df_tdur.copy()
                    df_tdur_viz['Total Seconds'] = pd.to_timedelta(df_tdur_viz['Total Durations']).dt.total_seconds()
                    fig = px.pie(df_tdur_viz, names='Channel Names', values='Total Seconds', hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_traces(textinfo='percent+label', textposition='outside')
                    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Content Durations Table"):
                        st.dataframe(df_tdur, use_container_width=True)
                else:
                    st.info("No duration data.")

            with col_avg_dur:
                st.subheader('Average Video Length')
                df_adur = channel_analysis.average_durations()
                if not df_adur.empty:
                    df_adur_viz = df_adur.copy()
                    df_adur_viz['Average Seconds'] = pd.to_timedelta(df_adur_viz['Average Durations']).dt.total_seconds()
                    fig = px.pie(df_adur_viz, names='Channel Names', values='Average Seconds', hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Bold)
                    fig.update_traces(textinfo='percent+label', textposition='outside')
                    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Average Length Table"):
                        st.dataframe(df_adur, use_container_width=True)
                else:
                    st.info("No duration data.")


class video_analysis:

    def total_video_names():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by video.video_id, channel.channel_name
                        order by channel.channel_name, video.video_name ASC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(s, columns=['Video Names', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_video_names_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where channel.channel_name = '{channel_name}'
                        group by video.video_id, channel.channel_name
                        order by video.video_name ASC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(s, columns=['Video Names', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_views():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.view_count, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by video.video_id, channel.channel_name
                        order by video.view_count DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Views', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_views_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.view_count, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where channel.channel_name = '{channel_name}'
                        group by video.video_id, channel.channel_name
                        order by video.view_count DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Views', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_likes():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.like_count, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by video.video_id, channel.channel_name
                        order by video.like_count DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Likes', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_likes_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.like_count, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where channel.channel_name = '{channel_name}'
                        group by video.video_id, channel.channel_name
                        order by video.like_count DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Likes', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_comments():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.comment_count, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by video.video_id, channel.channel_name
                        order by video.comment_count DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Comments', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_comments_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.comment_count, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where channel.channel_name = '{channel_name}'
                        group by video.video_id, channel.channel_name
                        order by video.comment_count DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Comments', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_comments_text():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, comment.comment_text, channel.channel_name
                        from comment
                        inner join video on video.video_id = comment.video_id
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by video.video_id, channel.channel_id, comment.comment_id
                        order by channel.channel_name, video.video_name, comment.comment_text ASC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Comment Names', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_comments_text_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, comment.comment_text, channel.channel_name
                        from comment
                        inner join video on video.video_id = comment.video_id
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where channel.channel_name = '{channel_name}'
                        group by video.video_id, channel.channel_id, comment.comment_id
                        order by channel.channel_name, video.video_name, comment.comment_text ASC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Comment Names', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_durations():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.duration, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by video.video_id, channel.channel_name
                        order by video.duration DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Durations', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df

    def total_durations_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select video.video_name, video.duration, channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where channel.channel_name = '{channel_name}'
                        group by video.video_id, channel.channel_name
                        order by video.duration DESC""")

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Total Durations', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df


    def engagement_rate():

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f'''select video.video_name,
                           round(((video.like_count + video.comment_count)::numeric
                                  / nullif(video.view_count, 0)) * 100, 2) as engagement,
                           channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        group by video.video_id, channel.channel_name
                        order by engagement DESC''')

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Engagement Rate (%)', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df


    def engagement_rate_select_channel(channel_name):

        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f'''select video.video_name,
                           round(((video.like_count + video.comment_count)::numeric
                                  / nullif(video.view_count, 0)) * 100, 2) as engagement,
                           channel.channel_name
                        from video
                        inner join playlist on playlist.upload_id = video.upload_id
                        inner join channel on channel.channel_id = playlist.channel_id
                        where channel.channel_name = \'{channel_name}\'
                        group by video.video_id, channel.channel_name
                        order by engagement DESC''')

        s = cursor.fetchall()
        i = [i for i in range(1, len(s) + 1)]
        df = pd.DataFrame(
            s, columns=['Video Names', 'Engagement Rate (%)', 'Channel Names'], index=i)
        df = df.rename_axis('S.No')
        df.index = df.index.map(lambda x: '{:^{}}'.format(x, 10))
        return df


    def main():
        st.subheader("📺 Video Level Deep Dive")
        channel_name = st.selectbox('Filter by Channel:', list_channel, key="vid_channel_select")

        # Fetch datasets dynamically based on channel selection
        if channel_name == 'Over All':
            df_views = video_analysis.total_views()
            df_likes = video_analysis.total_likes()
            df_comments = video_analysis.total_comments()
            df_comments_text = video_analysis.total_comments_text()
            df_durations = video_analysis.total_durations()
            df_engagement = video_analysis.engagement_rate()
        else:
            df_views = video_analysis.total_views_select_channel(channel_name)
            df_likes = video_analysis.total_likes_select_channel(channel_name)
            df_comments = video_analysis.total_comments_select_channel(channel_name)
            df_comments_text = video_analysis.total_comments_text_select_channel(channel_name)
            df_durations = video_analysis.total_durations_select_channel(channel_name)
            df_engagement = video_analysis.engagement_rate_select_channel(channel_name)

        tab1, tab2, tab3 = st.tabs([
            "📊 Video Performance", 
            "⚡ Engagement & Length", 
            "💬 Comments Explorer"
        ])

        with tab1:
            col_vws, col_lks = st.columns(2)
            with col_vws:
                st.subheader("👁️ Views by Video")
                if not df_views.empty:
                    df_vws_sorted = df_views.sort_values(by='Total Views', ascending=True)
                    fig = px.bar(df_vws_sorted, x='Total Views', y='Video Names', orientation='h',
                                 color='Total Views', color_continuous_scale='Tealgrn')
                    fig.update_layout(coloraxis_showscale=False, height=450)
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Table"):
                        st.dataframe(df_views, use_container_width=True)
                else:
                    st.info("No views data available.")

            with col_lks:
                st.subheader("❤️ Likes by Video")
                if not df_likes.empty:
                    df_lks_sorted = df_likes.sort_values(by='Total Likes', ascending=True)
                    fig = px.bar(df_lks_sorted, x='Total Likes', y='Video Names', orientation='h',
                                 color='Total Likes', color_continuous_scale='sunset')
                    fig.update_layout(coloraxis_showscale=False, height=450)
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Table"):
                        st.dataframe(df_likes, use_container_width=True)
                else:
                    st.info("No likes data available.")

        with tab2:
            col_cmts, col_eng = st.columns(2)
            with col_cmts:
                st.subheader("💬 Comment Count by Video")
                if not df_comments.empty:
                    df_cmts_sorted = df_comments.sort_values(by='Total Comments', ascending=True)
                    fig = px.bar(df_cmts_sorted, x='Total Comments', y='Video Names', orientation='h',
                                 color='Total Comments', color_continuous_scale='dense')
                    fig.update_layout(coloraxis_showscale=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Table"):
                        st.dataframe(df_comments, use_container_width=True)
                else:
                    st.info("No comments data available.")

            with col_eng:
                st.subheader("⚡ Engagement Rate (%)")
                if not df_engagement.empty:
                    df_eng_sorted = df_engagement.sort_values(by='Engagement Rate (%)', ascending=True)
                    fig = px.bar(df_eng_sorted, x='Engagement Rate (%)', y='Video Names', orientation='h',
                                 color='Engagement Rate (%)', color_continuous_scale='Bluered')
                    fig.update_layout(coloraxis_showscale=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 View Table"):
                        st.dataframe(df_engagement, use_container_width=True)
                else:
                    st.info("No engagement data available.")

            st.markdown("---")
            st.subheader("⏳ Video Duration Analysis")
            if not df_durations.empty:
                # Convert duration format to total minutes for plotting
                def to_minutes(time_obj):
                    try:
                        return time_obj.hour * 60 + time_obj.minute + time_obj.second/60.0
                    except:
                        try:
                            parts = str(time_obj).split(':')
                            return int(parts[0]) * 60 + int(parts[1]) + float(parts[2])/60.0
                        except:
                            return 0.0

                df_dur_viz = df_durations.copy()
                df_dur_viz['Duration (Minutes)'] = df_dur_viz['Total Durations'].apply(to_minutes)
                df_dur_viz_sorted = df_dur_viz.sort_values(by='Duration (Minutes)', ascending=True)

                fig = px.bar(df_dur_viz_sorted, x='Duration (Minutes)', y='Video Names', orientation='h',
                             color='Duration (Minutes)', color_continuous_scale='purples')
                fig.update_layout(coloraxis_showscale=False, height=450)
                st.plotly_chart(fig, use_container_width=True)
                with st.expander("📋 View Table"):
                    st.dataframe(df_durations, use_container_width=True)
            else:
                st.info("No duration data available.")

        with tab3:
            st.subheader("💬 Interactive Comments Explorer")
            if not df_comments_text.empty:
                video_list = sorted(df_comments_text['Video Names'].unique())
                selected_video = st.selectbox("Select a video to read its comments:", video_list)
                
                comments_for_vid = df_comments_text[df_comments_text['Video Names'] == selected_video]
                
                st.markdown(f"**Found {len(comments_for_vid)} comments for video:** *\"{selected_video}\"*")
                for index, row in comments_for_vid.iterrows():
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.05); padding: 1rem; border-left: 4px solid #8b5cf6; border-radius: 4px; margin-bottom: 0.75rem; color:#e5e7eb;">
                        💬 "{row['Comment Names']}"
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No comment text data available.")


streamlit_config()
st.write('')
st.write('')


with st.sidebar:


    option = option_menu(menu_title='', options=['Data Retrive from YouTube API', 'Store data to MongoDB',
                                                 'Migrating Data to SQL', 'Data Analysis', 'SQL Queries', 'Delete Channel Data', 'Exit'],
                         icons=['youtube', 'database-add', 'database-fill-check', 'list-task', 'pencil-square', 'trash', 'sign-turn-right-fill'])


if option == 'Data Retrive from YouTube API':

    try:

        # get input from user
        col1, col2 = st.columns(2, gap='medium')
        with col1:
            channel_id = st.text_input("Enter Channel ID: ")
        with col2:
            api_key = st.text_input("Enter Your API Key:", type='password')
        
        video_limit = st.slider("Select maximum videos to harvest:", min_value=1, max_value=500, value=10, step=5,
                                help="Harvesting fewer videos keeps it fast and saves your YouTube API quota.")
        
        submit = st.button(label='Submit')

        if submit and option is not None:

            api_service_name = "youtube"
            api_version = "v3"
            youtube = googleapiclient.discovery.build(api_service_name,
                                                    api_version, developerKey=api_key)

            data = {}
            final = youtube_extract.main(channel_id, video_limit)
            data.update(final)
            channel_name = data['channel']['channel_name']

            mongodb.drop_temp_collection()
            mongodb.data_storage(channel_name=channel_name,
                                 database='temp', data=final)

            # display the complete harvested data in streamlit
            st.json(final)
            st.success('Retrived data from YouTube successfully')
            st.balloons()

    except Exception as e:
        col1,col2 = st.columns([0.45,0.55])
        with col1:
            st.warning("Please enter the valid Channel ID and API key")
            st.exception(e)


elif option == 'Store data to MongoDB':
    mongodb.main('project_youtube')


elif option == 'Migrating Data to SQL':
    sql.main(mdb_database='project_youtube', sql_database='youtube')


elif option == 'Data Analysis':

    s1 = sql.list_channel_names()

    if s1 == []:
        st.info("The SQL database is currently empty")

    else:
        conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
        cursor = conn.cursor()

        cursor.execute(f"""select channel_name 
                                   from channel 
                                   order by channel_name ASC""")

        s = cursor.fetchall()
        list_channel = ['Over All']
        list_channel.extend([i[0] for i in s])
        st.subheader('Please Select one below:')
        analysis = ['Select one', 'Channels', 'Videos']

        select_analysis = st.selectbox('', analysis)
        if select_analysis == 'Channels':
            channel_analysis.main()
        elif select_analysis == 'Videos':
            video_analysis.main()


elif option == 'SQL Queries':
    s1 = sql.list_channel_names()
    if s1 == []:
        st.info("The SQL database is currently empty")
    else:
        sql_queries.main()


elif option == 'Delete Channel Data':
    st.subheader("🗑️ Delete Channel Data")
    st.markdown('<div class="query-card">⚠️ Use this interface to permanently remove a harvested channel from either your MongoDB Data Lake, PostgreSQL Data Warehouse, or both databases. This action is permanent and cannot be undone!</div>', unsafe_allow_html=True)
    
    # Fetch lists of channels in both databases
    mongo_channels = mongodb.list_collection_names('project_youtube')
    sql_channels = sql.list_channel_names()
    
    # Combine unique names
    all_channels = sorted(list(set(mongo_channels + sql_channels)))
    
    if not all_channels:
        st.info("No channels found in either MongoDB or PostgreSQL databases.")
    else:
        selected_channel = st.selectbox("Select Channel to Delete:", ["Select one"] + all_channels)
        
        if selected_channel != "Select one":
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Channel Location Status:**")
                in_mongo = "✅ Present in MongoDB" if selected_channel in mongo_channels else "❌ Not in MongoDB"
                in_sql = "✅ Present in PostgreSQL" if selected_channel in sql_channels else "❌ Not in PostgreSQL"
                st.write(in_mongo)
                st.write(in_sql)
            
            with col2:
                delete_target = st.radio("Choose database to delete from:", [
                    "Delete from BOTH (MongoDB & PostgreSQL)",
                    "Delete only from MongoDB NoSQL Lake",
                    "Delete only from PostgreSQL SQL Warehouse"
                ])
                
            st.warning(f"🚨 Are you absolutely sure you want to delete **'{selected_channel}'**? This will permanently wipe out all playlists, videos, and comments related to this channel from the selected database(s).")
            confirm_text = st.text_input(f"Type **CONFIRM** in all caps to unlock the delete button:")
            
            delete_btn = st.button("🔴 Permanently Delete Channel Data", disabled=(confirm_text != "CONFIRM"))
            
            if delete_btn:
                try:
                    # 1. MongoDB deletion
                    if "BOTH" in delete_target or "MongoDB" in delete_target:
                        if selected_channel in mongo_channels:
                            client = pymongo.MongoClient(st.secrets["MONGO_URI"])
                            db = client['project_youtube']
                            db.drop_collection(selected_channel)
                            st.success(f"🗑️ Collection '{selected_channel}' successfully dropped from MongoDB!")
                        else:
                            st.info("Channel was not present in MongoDB; skipped.")
                    
                    # 2. PostgreSQL deletion
                    if "BOTH" in delete_target or "PostgreSQL" in delete_target:
                        if selected_channel in sql_channels:
                            conn = psycopg2.connect(st.secrets["POSTGRES_URI"])
                            cursor = conn.cursor()
                            
                            # Fetch channel_id and upload_id
                            cursor.execute("select channel_id, upload_id from channel where channel_name = %s", (selected_channel,))
                            ch_row = cursor.fetchone()
                            if ch_row:
                                channel_id, upload_id = ch_row[0], ch_row[1]
                                
                                # Delete related comments first
                                cursor.execute("""
                                    delete from comment where video_id in (
                                        select video_id from video where upload_id = %s
                                    )
                                """, (upload_id,))
                                
                                # Delete related videos
                                cursor.execute("delete from video where upload_id = %s", (upload_id,))
                                
                                # Delete playlists
                                cursor.execute("delete from playlist where channel_id = %s", (channel_id,))
                                
                                # Delete channel row
                                cursor.execute("delete from channel where channel_id = %s", (channel_id,))
                                conn.commit()
                                st.success(f"🗑️ Row and all related videos/playlists/comments successfully deleted from PostgreSQL!")
                            else:
                                st.info("Could not fetch channel details from SQL; skipped.")
                            conn.close()
                        else:
                            st.info("Channel was not present in PostgreSQL; skipped.")
                    
                    st.success(f"🎉 Deletion operations completed successfully!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error executing deletion: {e}")


elif option == 'Exit':
    mongodb.drop_temp_collection()
    st.write('')
    st.write('')
    st.success('Thank you for your time. Exiting the application')
    st.balloons()
