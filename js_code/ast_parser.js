// jsファイルを読み込んでASTを生成
const esprima = require('esprima');
const fs = require('fs');

// コマンドライン引数からファイルパスを取得
const filePath = process.argv[2];
if (!filePath) {
    console.error('Usage: node ast_parser.js <path_to_js_file>');
    process.exit(1);
}

// ファイルを読み込んでASTに変換し、JSONとして標準出力に出力
try {
    const code = fs.readFileSync(filePath, 'utf-8');
    const ast = esprima.parseScript(code, { loc: true });
    console.log(JSON.stringify(ast, null, 2));
} catch (e) {
    console.error(`Error parsing file ${filePath}:`, e.message);
    process.exit(1);
}