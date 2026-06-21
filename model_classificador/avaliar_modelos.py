import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import StratifiedKFold, cross_validate, cross_val_predict
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc, precision_recall_curve, recall_score, precision_score
from statsmodels.stats.contingency_tables import mcnemar

# Imports do train_model e legado
import train_model
from legado.model_local_old import classificar_local as classificar_antigo

def main():
    print("Iniciando avaliação de modelos...")
    os.makedirs("graficos_tcc", exist_ok=True)
    
    # Obter dados
    df = train_model.df.copy()
    X = df["texto_clean"]
    y = df["classe"]
    y_bin = (y == "adulto").astype(int)
    
    # Modelos base para o TF-IDF da versão 4.0
    tfidf = train_model.pipeline.named_steps["tfidf"]
    
    modelos = {
        "Regressao Logistica (v4.0)": LogisticRegression(class_weight=None, max_iter=5000, C=2.0, solver='lbfgs'),
        "Naive Bayes (Multinomial)": MultinomialNB(),
        "SVM (Linear)": SVC(kernel='linear', probability=True, class_weight=None)
    }
    
    X_tfidf = tfidf.fit_transform(X)
    
    # 1. Comparação de 3 modelos (CV 5-fold)
    print("\n--- Comparação de Modelos (CV 5-fold) ---")
    resultados_modelos = {}
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for nome, clf in modelos.items():
        scoring = ['accuracy', 'precision_macro', 'recall_macro', 'f1_weighted']
        scores = cross_validate(clf, X_tfidf, y, cv=kf, scoring=scoring, n_jobs=-1)
        resultados_modelos[nome] = {
            "Acurácia": float(scores['test_accuracy'].mean()),
            "F1-Weighted": float(scores['test_f1_weighted'].mean())
        }
        print(f"{nome} - Acc: {scores['test_accuracy'].mean():.4f}, F1: {scores['test_f1_weighted'].mean():.4f}")
        
    # 2. Bootstrap 1000 iterações -> IC 95% do Recall e Precisão da classe adulta (usando RegLog)
    print("\n--- Bootstrap 1000 iterações (Regressão Logística) ---")
    n_iterations = 1000
    clf_escolhido = modelos["Regressao Logistica (v4.0)"]
    # Faz predict na base toda para o IC (não é rigoroso como OOF para toda iteração, mas serve para IC da performance final)
    # Para ser mais correto com o OOF, usaremos as predições OOF do RegLog:
    oof_preds = cross_val_predict(clf_escolhido, X_tfidf, y, cv=kf)
    oof_preds_bin = (oof_preds == "adulto").astype(int)
    
    boot_recalls = []
    boot_precisions = []
    indices = np.arange(len(y_bin))
    np.random.seed(42)
    for i in range(n_iterations):
        sample_idx = np.random.choice(indices, size=len(indices), replace=True)
        y_true_boot = y_bin.iloc[sample_idx]
        y_pred_boot = oof_preds_bin[sample_idx]
        boot_recalls.append(recall_score(y_true_boot, y_pred_boot, zero_division=0))
        boot_precisions.append(precision_score(y_true_boot, y_pred_boot, zero_division=0))
        
    ic_recall = (np.percentile(boot_recalls, 2.5), np.percentile(boot_recalls, 97.5))
    ic_precision = (np.percentile(boot_precisions, 2.5), np.percentile(boot_precisions, 97.5))
    
    print(f"Recall IC 95%: {ic_recall[0]:.4f} - {ic_recall[1]:.4f}")
    print(f"Precision IC 95%: {ic_precision[0]:.4f} - {ic_precision[1]:.4f}")
    
    # 3. Teste de McNemar (antigo vs novo)
    print("\n--- Teste de McNemar ---")
    # Novo: predições do pipeline completo (treinado em train_model.py)
    import joblib
    novo_pipeline = joblib.load("pipeline.pkl")
    # Carregando meta para pegar threshold
    with open("pipeline_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    thr = meta["threshold_adulto"]
    
    # Para o teste, vamos prever no dataset de teste de train_model.py ou o dataset todo?
    # Melhor em todo o dataset (OOF para o novo, direto para o antigo)
    y_true_all = (df["classe"] == "adulto").astype(int)
    
    # Antigo
    preds_antigo = df["texto"].apply(lambda t: classificar_antigo(t) == "adulto").astype(int)
    
    # Novo (OOF mas usando o thr customizado, vamos calcular as probas OOF e aplicar o thr)
    oof_probas = cross_val_predict(novo_pipeline, X, y, cv=kf, method='predict_proba')
    ia = list(novo_pipeline.classes_).index("adulto")
    preds_novo = (oof_probas[:, ia] >= thr).astype(int)
    
    # Contingency table
    # a: ambos corretos, b: antigo correto novo errado, c: antigo errado novo correto, d: ambos errados
    # Mas McNemar testa se as proporções de erros são diferentes, então as classes são "acertou" vs "errou"
    acerto_antigo = (preds_antigo == y_true_all).astype(int)
    acerto_novo = (preds_novo == y_true_all).astype(int)
    
    table = pd.crosstab(acerto_antigo, acerto_novo)
    print("Tabela de Contingência (Antigo x Novo, Erros x Acertos):")
    print(table)
    
    if table.shape == (2, 2):
        mc_result = mcnemar(table, exact=False, correction=True)
        print(f"McNemar p-value: {mc_result.pvalue:.4e}")
        p_mcnemar = mc_result.pvalue
    else:
        p_mcnemar = 1.0
        print("Tabela de contingência não é 2x2. Não é possível calcular McNemar.")

    # 4. Threshold sweep (0.3 a 0.8) -> precision/recall/FP frontier
    print("\n--- Threshold Sweep ---")
    thresholds = np.linspace(0.3, 0.8, 51)
    sweep_results = []
    for t in thresholds:
        p_bin = (oof_probas[:, ia] >= t).astype(int)
        r = recall_score(y_true_all, p_bin, zero_division=0)
        p = precision_score(y_true_all, p_bin, zero_division=0)
        fp = ((p_bin == 1) & (y_true_all == 0)).sum()
        sweep_results.append({"threshold": float(t), "precision": float(p), "recall": float(r), "FP": int(fp)})
    
    # 5. Gerar 3 figuras
    print("\n--- Gerando Figuras ---")
    
    # A) Matriz de Confusão
    # Para o holdout set (reproduzindo o split de train_model.py)
    from sklearn.model_selection import train_test_split
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
    y_pred_te = train_model.prever_com_limiar(novo_pipeline, X_te, thr)
    
    cm = confusion_matrix(y_te, y_pred_te, labels=novo_pipeline.classes_)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=novo_pipeline.classes_, yticklabels=novo_pipeline.classes_)
    plt.title(f'Matriz de Confusão (v4.0 @ limiar {thr:.2f})')
    plt.ylabel('Verdadeiro')
    plt.xlabel('Predito')
    plt.tight_layout()
    plt.savefig('graficos_tcc/confusion_matrix.png', dpi=300)
    plt.close()
    
    # B) ROC Curve (adulto vs outros) no test set
    probas_te = novo_pipeline.predict_proba(X_te)[:, ia]
    y_te_bin = (y_te == "adulto").astype(int)
    fpr, tpr, roc_thrs = roc_curve(y_te_bin, probas_te)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Taxa de Falsos Positivos')
    plt.ylabel('Taxa de Verdadeiros Positivos (Recall)')
    plt.title('Curva ROC - Classe Adulto (Test Set)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig('graficos_tcc/roc_curve.png', dpi=300)
    plt.close()
    
    # C) Precision-Recall curve
    precisions, recalls, pr_thrs = precision_recall_curve(y_te_bin, probas_te)
    plt.figure(figsize=(8, 6))
    plt.plot(recalls, precisions, color='blue', lw=2)
    plt.xlabel('Recall (Revocação)')
    plt.ylabel('Precision (Precisão)')
    plt.title('Curva Precision-Recall - Classe Adulto (Test Set)')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('graficos_tcc/precision_recall.png', dpi=300)
    plt.close()
    
    print("Figuras salvas em graficos_tcc/")
    
    # 6. Salvar avaliar_meta.json
    avaliar_meta = {
        "modelos_cv_5fold": resultados_modelos,
        "bootstrap_1000_reglog": {
            "recall_ic95": ic_recall,
            "precision_ic95": ic_precision
        },
        "mcnemar_p_value": p_mcnemar,
        "threshold_sweep_sample": sweep_results[::5] # salva a cada 0.05
    }
    with open("avaliar_meta.json", "w", encoding="utf-8") as f:
        json.dump(avaliar_meta, f, ensure_ascii=False, indent=2)
        
    print("Resultados salvos em avaliar_meta.json")

if __name__ == "__main__":
    main()
