import React, { useState, useCallback } from 'react'

export interface Toast {
  id: string
  title?: string
  description?: string
  action?: React.ReactNode
  variant?: 'default' | 'destructive'
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export interface ToastActionElement {
  altText: string
}

interface ToastState {
  toasts: Toast[]
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_VALUE
  return count.toString()
}

const listeners: Array<(state: ToastState) => void> = []
let memoryState: ToastState = { toasts: [] }

function dispatch(action: {
  type: 'ADD_TOAST' | 'UPDATE_TOAST' | 'DISMISS_TOAST' | 'REMOVE_TOAST'
  toast?: Partial<Toast>
}) {
  switch (action.type) {
    case 'ADD_TOAST':
      memoryState.toasts = [action.toast as Toast, ...memoryState.toasts]
      break
    case 'UPDATE_TOAST':
      memoryState.toasts = memoryState.toasts.map((t) =>
        t.id === action.toast?.id ? { ...t, ...action.toast } : t
      )
      break
    case 'DISMISS_TOAST': {
      const { id } = action.toast as { id: string }
      
      if (id) {
        addToRemoveQueue(id)
      } else {
        memoryState.toasts.forEach((toast) => {
          addToRemoveQueue(toast.id)
        })
      }

      memoryState.toasts = memoryState.toasts.map((t) =>
        t.id === id || id === undefined
          ? {
              ...t,
              open: false,
            }
          : t
      )
      break
    }
    case 'REMOVE_TOAST':
      if (action.toast?.id === undefined) {
        memoryState.toasts = []
      } else {
        memoryState.toasts = memoryState.toasts.filter((t) => t.id !== action.toast?.id)
      }
      break
  }

  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

function addToRemoveQueue(toastId: string) {
  if (toastTimeouts.has(toastId)) {
    return
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({
      type: 'REMOVE_TOAST',
      toast: { id: toastId },
    })
  }, 1000000)

  toastTimeouts.set(toastId, timeout)
}

export const reducer = (state: ToastState, action: any): ToastState => {
  switch (action.type) {
    case 'ADD_TOAST':
      return {
        ...state,
        toasts: [action.toast, ...state.toasts],
      }

    case 'UPDATE_TOAST':
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      }

    case 'DISMISS_TOAST': {
      const { id } = action.toast

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === id || id === undefined
            ? {
                ...t,
                open: false,
              }
            : t
        ),
      }
    }
    case 'REMOVE_TOAST':
      if (action.toast.id === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toast.id),
      }
    default:
      return state
  }
}

export function useToast() {
  const [state, setState] = useState<ToastState>(memoryState)

  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [state])

  const toast = useCallback(
    ({ ...props }: Omit<Toast, 'id'>) => {
      const id = genId()

      const update = (props: Partial<Toast>) =>
        dispatch({
          type: 'UPDATE_TOAST',
          toast: { ...props, id },
        })
      const dismiss = () => dispatch({ type: 'DISMISS_TOAST', toast: { id } })

      dispatch({
        type: 'ADD_TOAST',
        toast: {
          ...props,
          id,
          open: true,
          onOpenChange: (open: boolean) => {
            if (!open) dismiss()
          },
        },
      })

      return {
        id: id,
        dismiss,
        update,
      }
    },
    []
  )

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: 'DISMISS_TOAST', toast: { id: toastId } }),
  }
}
