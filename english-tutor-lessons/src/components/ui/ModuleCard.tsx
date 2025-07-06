// /src/components/ui/ModuleCard.tsx

import { Lock, PlayCircle, CheckCircle2, Zap } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ModuleProgress } from '@/services/tutorService';
import { cn } from '@/lib/utils';

// ... (ProgressBar sem alterações)

interface ModuleCardProps {
  module: ModuleProgress;
  isActive: boolean; // <-- PROP SIMPLIFICADA
  onStartLesson: (moduleId: string) => void;
  isLoading: boolean;
}

export function ModuleCard({ module, isActive, onStartLesson, isLoading }: ModuleCardProps) {
  const isCompleted = module.status === 'completed';
  // Um módulo está "bloqueado" se não estiver completo E não estiver ativo.
  const isLocked = !isCompleted && !isActive;

  let Icon = PlayCircle;
  let iconColor = 'text-blue-500';
  let buttonText = 'Continuar Módulo';

  if (isLocked) { Icon = Lock; iconColor = 'text-slate-400'; }
  else if (isCompleted) { Icon = CheckCircle2; iconColor = 'text-green-500'; }
  else if (isActive) {
    // Se está ativo, verificamos se é o começo de um novo módulo
    const isNewModule = module.progress.completed_lessons === 0;
    Icon = isNewModule ? Zap : PlayCircle;
    iconColor = isNewModule ? 'text-amber-500' : 'text-blue-500';
    buttonText = isNewModule ? 'Começar Novo Módulo' : 'Continuar Módulo';
  }

  return (
    <Card className={cn( "transition-all",
      isLocked && "bg-slate-50 opacity-60",
      isCompleted && "bg-green-50 border-green-200",
      isActive && "border-blue-500 ring-2 ring-blue-200"
    )}>
      <CardHeader className="flex-row items-start gap-4 space-y-0">
        <div className="flex-shrink-0"><Icon className={cn("h-8 w-8", iconColor)} /></div>
        <div className="flex-grow">
          <CardTitle>{module.title}</CardTitle>
          <CardDescription>{module.description}</CardDescription>
        </div>
      </CardHeader>

      <CardContent>
        {isActive && (
          <div className="space-y-2">
            {/* ... (lógica da barra de progresso) ... */}
            <Button className="w-full mt-4" onClick={() => onStartLesson(module.module_id)} disabled={isLoading}>
              {isLoading ? 'Aguarde...' : buttonText}
            </Button>
          </div>
        )}
        {isCompleted && <p className="text-sm font-semibold text-green-600">Módulo Concluído!</p>}
        {isLocked && <p className="text-sm font-semibold text-slate-500">Complete o módulo anterior para desbloquear.</p>}
      </CardContent>
    </Card>
  );
}