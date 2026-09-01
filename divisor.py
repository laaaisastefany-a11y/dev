import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Divisor de Contas", page_icon="💸")
st.title("💸 Divisor de Contas")
st.caption("Divida uma conta entre várias pessoas, de forma igual ou por item.")

def gerar_excel(resumo: dict, itens: list = None):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_resumo = pd.DataFrame(list(resumo.items()), columns=["Pessoa", "Valor a pagar (R$)"])
        df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
        if itens:
            df_itens = pd.DataFrame(itens)
            df_itens["pessoas"] = df_itens["pessoas"].apply(lambda p: ", ".join(p))
            df_itens.to_excel(writer, sheet_name="Itens", index=False)
        for pessoa in resumo:
            valor = resumo[pessoa]
            pd.DataFrame([{"Pessoa": pessoa, "Valor a pagar (R$)": valor}]).to_excel(
                writer, sheet_name=pessoa[:31], index=False
            )
    return output.getvalue()

# --- Passo 1: pessoas ---
st.header("1. Quem vai dividir a conta?")
if "pessoas" not in st.session_state:
    st.session_state.pessoas = ["Pessoa 1", "Pessoa 2"]
col1, col2 = st.columns([3, 1])
with col1:
    nova_pessoa = st.text_input("Nome da pessoa", key="nova_pessoa_input")
with col2:
    st.write("")
    st.write("")
    if st.button("Adicionar pessoa") and nova_pessoa.strip():
        st.session_state.pessoas.append(nova_pessoa.strip())
for i, pessoa in enumerate(st.session_state.pessoas):
    c1, c2 = st.columns([4, 1])
    c1.write(f"- {pessoa}")
    if c2.button("Remover", key=f"remover_{i}"):
        st.session_state.pessoas.pop(i)
        st.rerun()
if len(st.session_state.pessoas) < 2:
    st.warning("Adicione pelo menos 2 pessoas para dividir a conta.")
    st.stop()

# --- Passo 2: modo de divisão ---
st.header("2. Como dividir?")
modo = st.radio("Escolha o modo", ["Dividir igualmente", "Dividir por item"])

if modo == "Dividir igualmente":
    valor_total = st.number_input("Valor total da conta (R$)", min_value=0.0, step=1.0, format="%.2f")
    gorjeta_pct = st.slider("Gorjeta/serviço (%)", 0, 30, 10)
    if valor_total > 0:
        valor_com_gorjeta = valor_total * (1 + gorjeta_pct / 100)
        valor_por_pessoa = valor_com_gorjeta / len(st.session_state.pessoas)
        st.header("3. Resultado")
        st.metric("Total com gorjeta", f"R$ {valor_com_gorjeta:.2f}")
        st.metric("Valor por pessoa", f"R$ {valor_por_pessoa:.2f}")
        st.subheader("Resumo")
        for pessoa in st.session_state.pessoas:
            st.write(f"**{pessoa}**: R$ {valor_por_pessoa:.2f}")

        resumo = {p: valor_por_pessoa for p in st.session_state.pessoas}
        excel_bytes = gerar_excel(resumo)
        st.download_button("📥 Baixar planilha Excel", excel_bytes, "divisor_de_contas.xlsx")

else:  # Dividir por item
    st.write("Adicione os itens e quem consumiu cada um.")
    if "itens" not in st.session_state:
        st.session_state.itens = []
    with st.form("form_item", clear_on_submit=True):
        nome_item = st.text_input("Nome do item (ex: Pizza)")
        valor_item = st.number_input("Valor do item (R$)", min_value=0.0, step=1.0, format="%.2f")
        consumido_por = st.multiselect("Quem consumiu esse item?", st.session_state.pessoas)
        adicionar = st.form_submit_button("Adicionar item")
        if adicionar and nome_item and valor_item > 0 and consumido_por:
            st.session_state.itens.append({
                "nome": nome_item,
                "valor": valor_item,
                "pessoas": consumido_por
            })
    if st.session_state.itens:
        st.subheader("Itens adicionados")
        for i, item in enumerate(st.session_state.itens):
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{item['nome']}** — R$ {item['valor']:.2f} — {', '.join(item['pessoas'])}")
            if c2.button("Remover", key=f"remover_item_{i}"):
                st.session_state.itens.pop(i)
                st.rerun()
        gorjeta_pct = st.slider("Gorjeta/serviço (%)", 0, 30, 10, key="gorjeta_item")
        totais = {pessoa: 0.0 for pessoa in st.session_state.pessoas}
        for item in st.session_state.itens:
            valor_por_pessoa_item = item["valor"] / len(item["pessoas"])
            for pessoa in item["pessoas"]:
                totais[pessoa] += valor_por_pessoa_item
        fator_gorjeta = 1 + gorjeta_pct / 100
        totais_com_gorjeta = {p: v * fator_gorjeta for p, v in totais.items()}
        st.header("3. Resultado")
        st.metric("Total geral com gorjeta", f"R$ {sum(totais_com_gorjeta.values()):.2f}")
        st.subheader("Quanto cada um paga")
        for pessoa, valor in totais_com_gorjeta.items():
            st.write(f"**{pessoa}**: R$ {valor:.2f}")

        excel_bytes = gerar_excel(totais_com_gorjeta, st.session_state.itens)
        st.download_button("📥 Baixar planilha Excel", excel_bytes, "divisor_de_contas.xlsx")
    else:
        st.info("Nenhum item adicionado ainda.")