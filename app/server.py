import aiohttp
import asyncio
import uvicorn
import pandas as pd
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

export_file_url = 'https://drive.google.com/uc?export=download&id=1aCzT1JHiRrNogRk-V-Yi3jI_q2c-1_ea'
export_file_name = 'macro_export.pkl'

export_file_url_micro = 'https://drive.google.com/uc?export=download&id=1cV2PaYK_9xmVAyS7E_xqYeoKJgOlruRB'
export_file_name_micro = 'micro_export.pkl'




classes = ['amphib','carrier','corvette','destroyer','frigate','gunboat','mine','missile','subchaser','tender']
#classes_micro = ['arleigh_burke_destroyer', 'dayun_904_tender', 'fuchi_903_tender', 'fuqing_905_tender', 'fusu_908_tender', 'haiqing_037IS_subchaser', 'houbei_022_missile', 'houjian_houxin_037_missile', 'jiangdao_056_corvette', 'jianghu_053H1_frigate', 'jiangkai_II_054A_frigate', 'jiangkai_I_054_frigate', 'jiangwei_II_053H3_frigate', 'liaoning_001_carrier', 'luda_051_destroyer', 'luhai_051B_destroyer', 'luhu_052_destroyer', 'luyang_III_052D_destroyer', 'luyang_II_052C_destroyer', 'luyang_I_052B_destroyer', 'luzhou_051C_destroyer', 'renhai_055_destroyer', 'shanghai_III_062I_gunboat', 'sovremenny_956_destroyer', 'wasao_082_mine', 'wazang_082II_mine', 'wochi_081_mine', 'yubei_074A_amphib', 'yudeng_073III_amphib', 'yuhai_074_amphib', 'yukan_072_amphib', 'yunshu_073A_amphib', 'yuting_072II_amphib', 'yuting_III_072A_amphib', 'yuting_II_072III_amphib', 'yuzhao_071_amphib']

path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

ship_class_info = pd.read_csv('app/static/Ships_by_hull_number.csv', index_col = 0)
ship_class_info.sort_index(inplace = True)

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

async def setup_micro_learner():
    await download_file(export_file_url_micro, path / export_file_name_micro)
    try:
        learn_micro = load_learner(path, export_file_name_micro)
        return learn_micro
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
tasks_micro = [asyncio.ensure_future(setup_micro_learner())]
learn_micro = loop.run_until_complete(asyncio.gather(*tasks_micro))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))
    prediction = learn.predict(img)[0]
    #micro_prediction = learn_micro.predict(img)[0].replace('_', ' ')
    #prediction = 'big_predict'
    micro_prediction = 'little_predict'
    #micro_prediction = "Not currently implemented. Comments? email piazzr2@gmail.com"
    return JSONResponse({'result': str(prediction), 'result_micro':str(micro_prediction)})

@app.route('/hull_lookup', methods=['POST'])
async def hull_lookup(request):
    form_data = await request.form()
    hull_text = await (int(form_data['hull_text'].read()))
    try:
        info = ship_class_info.loc[hull_text,'Combined']
        #info = 'Test Text'
    except:
        info = 'Hull number is unknown'
    #micro_prediction = "Not currently implemented. Comments? email piazzr2@gmail.com"
    return JSONResponse({'hull_information': str(info)})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
