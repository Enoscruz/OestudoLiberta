"use client";

/**
 * Words Stagger — animação de entrada palavra por palavra (blur + deslocamento
 * + opacidade), conforme https://spell.sh/docs/words-stagger.
 *
 * O texto é recebido como children e dividido em palavras; cada palavra é um
 * `motion.span` com `variants` próprio, orquestrado pelo `staggerChildren`.
 */

import { motion, type Transition } from "motion/react";
import React from "react";

import { cn } from "@/lib/utils";

interface WordsStaggerProps {
  children: React.ReactNode;
  className?: string;
  /** Atraso antes da primeira palavra (segundos). */
  delay?: number;
  /** Intervalo entre palavras (segundos). */
  stagger?: number;
  /** Duração da animação de cada palavra (segundos). */
  speed?: number;
  /** Inicia a animação automaticamente na montagem. */
  autoStart?: boolean;
  onStart?: () => void;
  onComplete?: () => void;
  /** Dispara a animação quando o bloco entra na viewport. */
  inView?: boolean;
  once?: boolean;
}

export function WordsStagger({
  children,
  className,
  delay = 0,
  stagger = 0.1,
  speed = 0.5,
  autoStart = true,
  onStart,
  onComplete,
  inView = false,
  once = true,
}: WordsStaggerProps) {
  const text = React.Children.toArray(children)
    .filter((child) => typeof child === "string")
    .join("");

  const words = text.split(" ").filter((word) => word.length > 0);

  const transition: Transition = {
    type: "tween",
    ease: "easeOut",
    duration: speed,
  };

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: stagger,
        delayChildren: delay,
      },
    },
  };

  const wordVariants = {
    hidden: {
      opacity: 0,
      y: 10,
      filter: "blur(10px)",
    },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition,
    },
  };

  return (
    <motion.div
      className={cn("flex flex-wrap", className)}
      variants={containerVariants}
      initial="hidden"
      whileInView={inView ? "visible" : undefined}
      animate={inView ? undefined : autoStart ? "visible" : "hidden"}
      viewport={{ once }}
      onAnimationStart={onStart}
      onAnimationComplete={onComplete}
    >
      {words.map((word, index) => (
        <motion.span key={`${word}-${index}`} className="inline-block" variants={wordVariants}>
          {word}
          {index < words.length - 1 && <span className="inline-block">&nbsp;</span>}
        </motion.span>
      ))}
    </motion.div>
  );
}
