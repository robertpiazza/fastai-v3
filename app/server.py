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


#classes = ['amphib','carrier','corvette','destroyer','frigate','gunboat','mine','missile','subchaser','tender']
classes_micro = ['arleigh_burke_destroyer', 'dayun_904_tender', 'fuchi_903_tender', 'fuqing_905_tender', 'fusu_908_tender', 'haiqing_037IS_subchaser', 'houbei_022_missile', 'houjian_houxin_037_missile', 'jiangdao_056_corvette', 'jianghu_053H1_frigate', 'jiangkai_II_054A_frigate', 'jiangkai_I_054_frigate', 'jiangwei_II_053H3_frigate', 'liaoning_001_carrier', 'luda_051_destroyer', 'luhai_051B_destroyer', 'luhu_052_destroyer', 'luyang_III_052D_destroyer', 'luyang_II_052C_destroyer', 'luyang_I_052B_destroyer', 'luzhou_051C_destroyer', 'renhai_055_destroyer', 'shanghai_III_062I_gunboat', 'sovremenny_956_destroyer', 'wasao_082_mine', 'wazang_082II_mine', 'wochi_081_mine', 'yubei_074A_amphib', 'yudeng_073III_amphib', 'yuhai_074_amphib', 'yukan_072_amphib', 'yunshu_073A_amphib', 'yuting_072II_amphib', 'yuting_III_072A_amphib', 'yuting_II_072III_amphib', 'yuzhao_071_amphib']

path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner_macro():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn_macro = load_learner(path, export_file_name)
        return learn_macro
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

async def setup_learner_micro():
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
tasks_micro = [asyncio.ensure_future(setup_learner_micro())]
learn_micro = loop.run_until_complete(asyncio.gather(*tasks_micro))[0]
tasks_macro = [asyncio.ensure_future(setup_learner_macro())]
learn_macro = loop.run_until_complete(asyncio.gather(*tasks_macro))[0]
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
    macro_prediction = learn_macro.predict(img)
    prediction = f"{str(macro_prediction[0]).title()} ({round(macro_prediction[2].max().item()*100)}% Probability)"
    #micro_prediction = str(learn_micro.predict(img)[0]).replace('_', ' ')
    #make predictions for individual classes
    micro_prediction = learn_micro.predict(img)
    result_micro_text = str(micro_prediction[0]).replace('_',' ').title().replace("Iii", "III").replace("Ii",'II')
    result_micro = f"{result_micro_text} ({round(micro_prediction[2].max().item()*100)}% Probability)"
    #combine labels and probabilities
    micro_predictions_df = pd.DataFrame({"Probability":micro_prediction[2].tolist(), "Classes":learn_micro.data.classes})
    #find top 5
    top_5 = micro_predictions_df.sort_values(by="Probability", ascending = False).head()
    #create combined labels and probabilites
    top_5['Class and Probability'] = (top_5.Classes.str.replace('_',' ')+' ('+((top_5.Probability*100).round()).map(int).map(str)+'%)').apply(lambda x: x.title().replace("Iii", "III").replace("Ii",'II'))
    #capitalize each word and make sure versions stay good
    #top_5_results = ", ".join(top_5.Combined.tolist()).title().replace("Iii", "III").replace("Ii",'II')
    top_5_results = top_5[['Class and Probability']].to_html(index = False)
    #micro_prediction = micro_prediction
    #prediction = 'big_predict'
    #micro_prediction = 'Not currently implemented.'
    #micro_prediction = "Not currently implemented. Comments? email piazzr2@gmail.com"
    return JSONResponse({'result': prediction, 'result_micro':result_micro, 'top_5':top_5_results})

@app.route('/hull_lookup', methods=['POST'])
async def hull_lookup(request):
    try:
        pd.set_option('display.max_colwidth', -1)
        form_data = await request.form()
        hull_text = form_data['hull_text']
        ship_class_info = pd.read_csv(path / 'static/Ships_by_hull_number.csv', index_col = 0)
        ship_class_info.index = ship_class_info.index.rename("Hull Number")
        ship_class_info.columns = ['Information', 'Type', 'Nato Designation', 'Pennant No.', 'Name', 'Name.1',
       'Commissioned', 'Tons', 'Fleet', 'Status']
        ship_class_info["Pennant No."] = ship_class_info["Pennant No."].fillna(0).map(int)
        info = ship_class_info.loc[int(hull_text):int(hull_text),['Pennant No.', 'Information']].to_html(index = False)
    except:
        info = 'Hull number is unknown or ship is no longer active'
    #micro_prediction = "Not currently implemented. Comments? email piazzr2@gmail.com"
    return JSONResponse({'hull_information': str(info)})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
