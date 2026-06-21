import json
import os
import pandas as pd
from dados_simulacao import CORPUS
from legado.model_local_old import classificar_local as classificar_antigo
from ia.model_local import classificar_local as classificar_novo

def classificar_binario(classificacao):
    return "adulto" if classificacao == "adulto" else "nao_adulto"

def calcular_metricas(resultados):
    tp = sum(1 for r in resultados if r['verdadeiro'] == 'adulto' and r['predito'] == 'adulto')
    fp = sum(1 for r in resultados if r['verdadeiro'] == 'nao_adulto' and r['predito'] == 'adulto')
    tn = sum(1 for r in resultados if r['verdadeiro'] == 'nao_adulto' and r['predito'] == 'nao_adulto')
    fn = sum(1 for r in resultados if r['verdadeiro'] == 'adulto' and r['predito'] == 'nao_adulto')
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    return {
        "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "precision": precision, "recall": recall, "specificity": specificity
    }

def main():
    print(f"Simulando ambiente com {len(CORPUS)} posts...")
    
    resultados_antigo = []
    resultados_novo = []
    fps_reduzidos = []
    
    for texto, rotulo_binario, grupo in CORPUS:
        pred_antigo = classificar_binario(classificar_antigo(texto))
        pred_novo = classificar_binario(classificar_novo(texto))
        
        resultados_antigo.append({
            "texto": texto, "verdadeiro": rotulo_binario, "predito": pred_antigo, "grupo": grupo
        })
        resultados_novo.append({
            "texto": texto, "verdadeiro": rotulo_binario, "predito": pred_novo, "grupo": grupo
        })
        
        # Exemplo de FP reduzido: Antigo classificava como adulto (errado) e novo como não_adulto (certo)
        if rotulo_binario == "nao_adulto" and pred_antigo == "adulto" and pred_novo == "nao_adulto":
            fps_reduzidos.append({"texto": texto, "grupo": grupo})
            
    # Calcular Métricas
    metrics_antigo = calcular_metricas(resultados_antigo)
    metrics_novo = calcular_metricas(resultados_novo)
    
    print("\n--- Relatório de Simulação ---")
    print(f"{'Métrica':<15} | {'Modelo Antigo (v3.0)':<20} | {'Modelo Novo (v4.0)':<20}")
    print("-" * 60)
    print(f"{'True Positives':<15} | {metrics_antigo['TP']:<20} | {metrics_novo['TP']:<20}")
    print(f"{'False Positives':<15} | {metrics_antigo['FP']:<20} | {metrics_novo['FP']:<20}")
    print(f"{'True Negatives':<15} | {metrics_antigo['TN']:<20} | {metrics_novo['TN']:<20}")
    print(f"{'False Negatives':<15} | {metrics_antigo['FN']:<20} | {metrics_novo['FN']:<20}")
    print("-" * 60)
    print(f"{'Precision':<15} | {metrics_antigo['precision']:.4f}               | {metrics_novo['precision']:.4f}")
    print(f"{'Recall':<15} | {metrics_antigo['recall']:.4f}               | {metrics_novo['recall']:.4f}")
    print(f"{'Specificity':<15} | {metrics_antigo['specificity']:.4f}               | {metrics_novo['specificity']:.4f}")
    
    print(f"\nNúmero de Falsos Positivos corrigidos pelo novo modelo: {len(fps_reduzidos)}")
    print("\nExemplos de FP reduzidos (classificados corretamente pelo novo):")
    import random
    amostras_fps = random.sample(fps_reduzidos, min(5, len(fps_reduzidos)))
    for ex in amostras_fps:
        print(f" - [{ex['grupo']}] {ex['texto']}")
        
    # Salvar resultados
    simulacao_resultados = {
        "antigo_v3": metrics_antigo,
        "novo_v4": metrics_novo,
        "total_posts": len(CORPUS),
        "total_adulto_real": sum(1 for _, r, _ in CORPUS if r == "adulto"),
        "fps_corrigidos_count": len(fps_reduzidos),
        "fps_corrigidos_exemplos": fps_reduzidos[:10]
    }
    
    with open("simulacao_resultados.json", "w", encoding="utf-8") as f:
        json.dump(simulacao_resultados, f, ensure_ascii=False, indent=2)
        
    print("\nResultados salvos em simulacao_resultados.json")

if __name__ == "__main__":
    main()
