"""Export the frozen ImageNet backbone (feature extractor) to ONNX for in-browser use.
The backbone is never fine-tuned; only the small head in model/head.json is trained.
"""
import os, json, torch, timm
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model')
NAME = os.environ.get('BACKBONE', 'mobilenetv3_large_100')
m = timm.create_model(NAME, pretrained=True, num_classes=0).eval()
cfg = m.pretrained_cfg
x = torch.randn(1, 3, 224, 224)
with torch.no_grad():
    d = m(x).shape[1]
path = os.path.join(OUT, 'backbone.onnx')
torch.onnx.export(m, x, path, input_names=['input'], output_names=['embedding'],
                  dynamic_axes={'input': {0: 'n'}, 'embedding': {0: 'n'}}, opset_version=17, dynamo=False)
meta = {'backbone': NAME, 'embed_dim': int(d), 'input_size': 224, 'resize_shorter': 256,
        'mean': list(cfg['mean']), 'std': list(cfg['std']), 'license': cfg.get('license', 'apache-2.0'),
        'onnx_bytes': os.path.getsize(path)}
json.dump(meta, open(os.path.join(OUT, 'backbone_meta.json'), 'w'), indent=1)
print(meta)
